import json
import os

# try to import modules for python3, if failed, fallback to python2
try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError

from lxml import etree
from io import open


def get_orcid_citations(config):
    """
    This method is using ORCID public API in order to obtain XML document representing each person's profile.
    It is then parsed to get all listed citations.
    They are then distinguished based on weather they are entered in bibtex format or presumably pre-formatted .

    :param config: object representing the configuration file specifying parameters of the job
    """

    # dict of String - Integer of how many non-bibtex citations given person has
    unspecified_format = dict()

    orcids = json.loads(config.get("orcid", "ids_to_check"))
    if not orcids:
        return

    for keyval in orcids:
        # this is due to the way the json is structured;
        # each person is represented as an object with single attribute person : orcid;
        for person, orcid in keyval.items():
            print("[Orcid] Getting citations for " + person)
            unspecified_format[person] = 0
            url = config.get("orcid", "BASE_ORCID_API_URL") + orcid + config.get("orcid", "ORCID_WORKS_URL")
            try:
                works_xml_string = urlopen(url).read()
            except HTTPError:
                print("There are no orcid records for " + person)
                continue

            xml_parse_tree = etree.fromstring(works_xml_string)

            citation_file_name = os.path.join("citations", "".join(person.split()) + "_fromORCID.bib")
            with open(citation_file_name, "w", encoding="utf-8") as citation_file:
                for work_citation in xml_parse_tree.xpath('//*[local-name()="work-citation"]'):
                    work_citation_type = work_citation[0].text
                    citation = work_citation[1].text + "\n"

                    citation = citation.encode("utf-8").decode("utf-8")
                    citation_file.write(citation)

                    if not work_citation_type == 'bibtex':
                        unspecified_format[person] += 1

    total_unspecified = sum(unspecified_format.values())
    if total_unspecified:
        print("ORCID " + str(total_unspecified) +
              " citation(s) were entered in an unspecified format. Assuming they are valid citations\nBreakdown:")
        for person, count in unspecified_format.items():
            print(person + ": " + str(count))
