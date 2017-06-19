import json
import os

# try to import modules for python3, if failed, fallback to python2
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from lxml import etree
from io import open


def get_search_name_string(name):
    """
    Formats the name of an author to be searchable using pubmed public API

    :param name: name of the person whose records are being searched
    :return: formatted part of the search url

    :todo: support for names with different structure than FirstName LastName
    """
    first_name, last_name = tuple(name.split(' '))
    return last_name + ",%20" + first_name + "[Full%20Author%20Name]"


def get_pubmed_citations(config):
    """
    This method is using ncbi public API in order to obtain XML document representing each person's profile.
    It is then parsed to get ids of all works (co-)published by the person.
    Then another query is performed in order to get publication details for the works specified

    :param config: object representing the configuration file specifying parameters of the job
    """

    people = json.loads(config.get("pubmed", "people_to_check"))
    for person in people:
        print("[PubMed] Getting citations for " + person)
        search_url = config.get("pubmed", "BASE_SEARCH_URL") + get_search_name_string(person)
        uids_xml_string = urlopen(search_url).read()
        uid_xml_parse_tree = etree.fromstring(uids_xml_string)
        uid_search_string = ""

        for uid in uid_xml_parse_tree.xpath('//Id'):
            uid_search_string = uid_search_string + uid.text + ","

        if not uid_search_string:
            print(person + " does not have any publications on PubMed")
            continue  # there are no works for the given person on ncbi

        uid_search_string = uid_search_string[:-1]  # removes comma at the end
        uid_search_url = config.get("pubmed",
                                    "BASE_INFO_URL") + uid_search_string + "&retmode=xml"  # requests the response to contain xml file which is way easier to parse

        works_xml_string = urlopen(uid_search_url).read()
        works_xml_parse_tree = etree.fromstring(works_xml_string)

        # transforms the part of xml tree containing cited works to be bibtex-like formatted
        xslt_root = etree.parse('pubmed2bibtex.xsl')
        transform = etree.XSLT(xslt_root)
        bibtex_data = transform(works_xml_parse_tree)
        bibtex_data = str(bibtex_data)  # etree.tostring(bibtex_data)
        try:
            bibtex_data = bibtex_data.decode("utf-8")  # python 2
        except AttributeError:
            pass  # python 3

        citation_file_name = os.path.join("citations", "".join(person.split()) + "_fromPubmed.bib")
        with open(citation_file_name, "w", encoding="utf-8") as citation_file:
            citation_file.write(bibtex_data)
