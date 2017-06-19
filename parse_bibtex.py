import os
import re
import shutil
import subprocess
import sys
from io import open

import pybtex
import pybtex.database

bibtex2html_directory = "bibtex2html"


def parse_mixed_source(source_file):
    """
    Tries to parse file which may contain citations with mixed formatting,
    i.e. some can be in bibtex and some may be already pre-formatted.

    :param source_file: file containing the citations
    :return: tuple with lists of strings with bibtex and nonbibtex citations
    """
    bibtex_citations = list()
    non_bibtex_citations = list()
    with open(source_file, "r", encoding="utf-8") as citations_source_file:
        current_citation = ""
        lbc = 0
        rbc = 0
        is_bibtex = False
        is_citation_over = False

        # firstly, clean up the input data
        datalines = list(line.rstrip('\r\n') for line in citations_source_file)
        for idx, line in enumerate(datalines):
            if line == "" or line == "\n":  # removes empty datalines
                datalines.pop(idx)

        # then goes line by line of the file to identify individual citations
        for line in datalines:
            current_citation += line
            line_length = len(line)
            for idx, ch in enumerate(line):
                if ch == "@" and idx == 0:  # if line begins with @ sign, we can assume with high probability that it is a bibtex citation
                    is_bibtex = True
                    is_citation_over = False

                # since bibtex citation can span for multiple lines, it is over once braces are balanced
                if is_bibtex:
                    if ch == "{":
                        lbc += 1
                    if ch == "}":
                        rbc += 1
                    if lbc == rbc and (lbc, rbc) != (0, 0):
                        is_citation_over = True

                if idx == (line_length - 1):  # scanned whole line
                    # we assume that if the citation is not bibtex, it is already pre-formatted and can only span for a single line
                    if not is_bibtex:
                        is_citation_over = True

                    if is_citation_over:
                        current_citation = re.sub('\s+', ' ',
                                                  current_citation).strip()  # cleans up the citation from double spaces, tabs, etc
                        if not is_bibtex:
                            non_bibtex_citations.append(current_citation)
                        else:
                            bibtex_citations.append(current_citation)

                        # resets all flags, counters, etc for the next citation in the file
                        current_citation = ""
                        lbc = 0
                        rbc = 0
                        is_bibtex = False
                        is_citation_over = False

    return bibtex_citations, non_bibtex_citations


unique_cite_keys = set()


# for re.sup (much easier to read than the lambda would have been otherwise for same purpose)
# say "Turing1950" key is used by two independent citations, then the second one is changed to "Turing1950a"
def fix_citation_keys(matchobj):
    """
    Used as an auxiliary method in remove_bibtex_duplicates() method;
    used in order to make correct substitutions in possibly duplicate bibtex citation keys

    :param matchobj: matched object in the regex (in that case a bibtex citation key)
    :return: adjusted (or not) bibtex citation key
    """
    cleaned_cite_key = matchobj.group(2).lstrip()
    temp_citation_key = cleaned_cite_key
    while temp_citation_key in unique_cite_keys:
        temp_citation_key += "a"

    unique_cite_keys.add(temp_citation_key)
    return matchobj.group(1) + temp_citation_key + matchobj.group(3)


def remove_bibtex_duplicates(combined_bibtex_file):
    """
    Tries to remove duplicate entries from bibtex citations
    In order to do this, it uses pybtex library that parse the citations

    :param combined_bibtex_file:
    :return:
    """

    # firstly ensures unique citation keys for easier manipulation (and because pybtex would throw an exception otherwise)
    with open(combined_bibtex_file, 'r', encoding='utf-8') as combined_bibtex:
        unique_keys_data = re.sub(r'(@.*?\{)(.+?)(,)', fix_citation_keys,
                                  combined_bibtex.read())  # bibtex citation key is second group of that regex: (@cite_type)(cite_key)(,)

    with open(combined_bibtex_file, 'w', encoding='utf-8') as combined_bibtex:
        combined_bibtex.write(unique_keys_data)

    bib_data = pybtex.database.parse_file(combined_bibtex_file)

    citation_keys = list()
    for citation_key in bib_data.entries:
        citation_keys.append(citation_key)

    entry_year = dict()
    entries_to_exclude = set()
    unique_titles = set()
    for citation_key in citation_keys:
        try:
            entry_year[citation_key] = bib_data.entries[citation_key].fields['year']
            if entry_year[citation_key] == '' or entry_year[citation_key] == ' ':
                entry_year[citation_key] = 'none'
        except KeyError:
            entry_year[citation_key] = 'none'
        title = bib_data.entries[citation_key].fields['title']
        while title[0] == '{' and title[-1] == '}':  # some titles had double brackets, i.e. {{someTitle}}
            title = title[1:-1]
        if title not in unique_titles:
            unique_titles.add(title)
        else:
            entries_to_exclude.add(
                citation_key)  # if multiple entries have same title, it is safe to assume they represent same publications

    return entries_to_exclude, entry_year


def remove_nonbibtex_duplicates(combined_nonbibtex_file):
    """
    Tries to remove duplicate entries from nonbibtex entries.
    There is not much there can be done trivially appart from checking if data lines are identical.

    Possible improvement might include trying to extract title of publication in order to compare those instead.

    :param combined_nonbibtex_file: file containing the citations
    """

    lines_seen = set()  # holds lines already seen
    out_lines = list()  # final lines to output
    with open(combined_nonbibtex_file, "r", encoding='utf-8') as combined_nonbibtex:
        for line in combined_nonbibtex:
            if line not in lines_seen:  # not a duplicate
                lines_seen.add(line)
                out_lines.append(line)
    if out_lines:
        with open(combined_nonbibtex_file, "w", encoding='utf-8') as combined_nonbibtex:
            info_str = ""
            try:
                info_str = ("Following need to be manually inserted: \n\n").decode("utf-8")
            except AttributeError:
                info_str = "Following need to be manually inserted: \n\n"

            combined_nonbibtex.write(info_str)

            for item in out_lines:
                combined_nonbibtex.write("<li> %s </li> \n" % item.rstrip(
                    '\r\n'))  # makes it into a list as it will be put inside a html file; Possible todo, if theres need for it: make it a variable


def combine_citation_files(combined_bibtex_file, combined_non_bibtex_file):
    """
    Combines all the previously generated bibtex-citation files to html files divided by publication year

    :param combined_bibtex_file:
    :param combined_non_bibtex_file:
    """

    # there are no citations files, no point in running the procedure
    if not os.listdir("citations"):
        raise IOError

    with open(combined_bibtex_file, "w", encoding='utf-8') as combined_bibtex:
        with open(combined_non_bibtex_file, "w", encoding='utf-8') as combined_nonbibtex:
            for file in os.listdir("citations"):
                if file.endswith(
                        "ORCID.bib"):  # gscholar and pubmed guarantee consistent structures, only ORCID doesn't because people enter their works themselves; if required can be extended with extra clauses
                    (bibtex_citations, nonbibtex_citations) = parse_mixed_source(os.path.join("citations", file))
                    for bibtex_citation in bibtex_citations:
                        bibtex_citation += "\n"
                        bibtex_citation = bibtex_citation

                        combined_bibtex.write(bibtex_citation)

                    for nonbibtex_citation in nonbibtex_citations:
                        nonbibtex_citation += "\n"
                        nonbibtex_citation = nonbibtex_citation
                        combined_nonbibtex.write(nonbibtex_citation)

        for file in os.listdir("citations"):
            if not file.endswith("ORCID.bib"):  # same reason as before
                combined_bibtex.write(open(os.path.join("citations", file), 'r', encoding='utf-8').read())

    with open(combined_bibtex_file, 'r', encoding='utf-8') as combined_bibtex:
        bibtex_data = combined_bibtex.read()

    # even though APA ignores months, let's make the converter not throw warnings of incorrect format, so that it would work if the citation style changed:
    rep = {"{\\textquotesingle}": "'",
           "{\\textperiodcentered}": "{\cdot}",
           "{\\textgreater}": "$>$",
           "{\\textless}": "%<%",
           "{\$}\\backslashvarepsilon{\$}": "$\\varepsilon$",
           "\\upbeta": "\\beta",
           "{jan}": "jan",
           "{feb}": "feb",
           "{mar}": "mar",
           "{apr}": "apr",
           "{may}": "may",
           "{jun}": "jun",
           "{jul}": "jul",
           "{aug}": "aug",
           "{sep}": "sep",
           "{oct}": "oct",
           "{nov}": "nov",
           "{dec}": "dec",
           }
    # perform the replacement
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    new_bibtex_data = pattern.sub(lambda m: rep[re.escape(m.group(0))], bibtex_data)

    with open(combined_bibtex_file, 'w', encoding='utf-8') as combined_bibtex:
        combined_bibtex.write(new_bibtex_data)


def parse_bibtex(config):
    """
    Parses the obtained citation files by first combining them together and trying to remove duplicates.
    They are then separated by year and corresponding html files are generated
    To do it, it uses the bibtex2html tool created by Jean-Christophe Filliatre (https://github.com/backtracking/bibtex2html)

    :param config: object representing the configuration file specifying parameters of the job
    """

    combined_directory = "combined"

    output_directory = config.get('bibtex', 'output_directory')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    combined_bibtex_file = os.path.join(combined_directory, "combined_bibtex.bib")
    combined_nonbibtex_file = os.path.join(output_directory, "combined_nonbibtex_citations.txt")

    if not os.path.exists(combined_directory):
        os.makedirs(combined_directory)

    # if there are no citations files to combine, throw exception up, so that the script would not try to clean html which does and will not exist
    try:
        combine_citation_files(combined_bibtex_file, combined_nonbibtex_file)
    except IOError as e:
        print("There are no citations files to combine")
        raise e

    remove_nonbibtex_duplicates(combined_nonbibtex_file)
    (entries_to_exclude, entry_year) = remove_bibtex_duplicates(combined_bibtex_file)

    platform_run_on = sys.platform
    if not platform_run_on.startswith('linux') and platform_run_on != 'win32' and platform_run_on != 'darwin':
        print("You are trying to run the script on an unrecognised platform. It will terminate now.")
        sys.exit(1)

    if platform_run_on == 'darwin':
        print("Warning: You are running the script on Mac OS X. It has not been tested on that platform.")

    entries_by_year = dict()
    for entry, year in entry_year.items():
        if year not in entries_by_year:
            entries_by_year[year] = set()
        if entry not in entries_to_exclude:
            entries_by_year[year].add(entry)

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    for year, entries in entries_by_year.items():
        tmp_file_directory = os.path.join('tmp', "year" + year)
        if not os.path.exists(tmp_file_directory):
            os.makedirs(tmp_file_directory)

        tmp_file_name = 'citefile.tmp'
        tmp_file_location = os.path.join(tmp_file_directory, tmp_file_name)

        with open(tmp_file_location, "w", encoding='utf-8') as tmp_file:
            for entry in entries:
                tmp_file_content = (entry + "\n").encode("utf-8").decode("utf-8")
                tmp_file.write(tmp_file_content)

        given_output_file = os.path.join(output_directory, 'output' + year)
        citation_style_file = config.get("bibtex", "citation_style_file")

        # for some reason the application does not correctly recognise style files if they are passed with the extension
        if citation_style_file.endswith(".bst"):
            citation_style_file = citation_style_file[:-4]

        citation_style_file_location = os.path.join(bibtex2html_directory, citation_style_file)

        bibtex2html_executable = ""
        if platform_run_on.startswith('linux'):
            bibtex2html_executable = "bibtex2html_linux"
        elif platform_run_on == "win32":
            bibtex2html_executable = "bibtex2html_win32"
        elif platform_run_on == "darwin":
            bibtex2html_executable = "bibtex2html_osx"

        bibtex2html_executable_location = os.path.join(bibtex2html_directory, bibtex2html_executable)

        args = [bibtex2html_executable_location,
                '-o',
                given_output_file,
                '-s',
                citation_style_file_location,
                '-nokeys',
                '-nodoc',
                '-nobibsource',
                '-nokeywords',
                '-noabstract',
                '-noheader',
                '-d',
                '-i',
                '-citefile',
                tmp_file_location,
                combined_bibtex_file]

        subprocess.call(args)

    # after finished, remove the created tmp directory (and its contents)
    shutil.rmtree('tmp')


def is_valid_paragraph(paragraph):
    if re.search(u'[\u4e00-\u9fff]', paragraph) or 'bibtex2html' in paragraph:
        return False
    return True


def clean_up_html():
    """
    Cleans up the created html files (removes extra newlines, changes paragraphs into lists, etc)

    """
    for output_file in os.listdir("output"):
        output_file = os.path.join("output", output_file)
        with open(output_file, "r", encoding='ISO-8859-1') as html_file:
            html_file_content = html_file.read()

            cleaned_html = '<p>'.join(filter(lambda s: is_valid_paragraph(s), html_file_content.split(
                '<p>')))  # removes entries with chinese text; can be extended to any unicode range + final paragraph with: created using.... # for future reference: regex doing the same job: r'(?s)(?:<p>.*?</p>.*?)*(<p>.*?(?:[\u4e00-\u9fff]+.*[\u4e00-\u9fff]+)+.*?</p>
            cleaned_html = re.sub(r'<hr>', '', cleaned_html, 0)  # removes the remaining <hr> tag at the end
            cleaned_html = re.sub(r'<a name=\".*></a>', '', cleaned_html,
                                  0)  # removes the anchors with bibtex citation keys

            cleaned_html = re.sub(r'(\n)*<p>(\n)*', '<li>', cleaned_html,
                                  0)  # changes paragraphs into list elements; opening tags
            cleaned_html = re.sub(r'(\n)*</p>(\n)*', '</li>\n\n', cleaned_html,
                                  0)  # changes paragraphs into list elements; closing tags

            cleaned_html = '<ul>\n' + cleaned_html.rstrip() + '\n</ul>'

            # for if there was a need to replace particular strings/characters in the output html code
            # rep = {"`": "'",
            #
            #        }
            #
            # rep = dict((re.escape(k), v) for k, v in rep.items())
            # pattern = re.compile("|".join(rep.keys()))
            # cleaned_html = pattern.sub(lambda m: rep[re.escape(m.group(0))], cleaned_html)
            #
            # replaces unicode characters their ascii equivalents
            # cleaned_html = unicodedata.normalize('NFKD', cleaned_html).encode('ascii', 'ignore').decode('utf-8')

        with open(output_file, "w", encoding='ISO-8859-1') as html_file:
            html_file.write(cleaned_html)
