#!/usr/bin/python
"""
These scripts are designed for querying various academic resources
in order to get list of all published works by specified, in the
configuration file, people.
"""

# Changelog
# ---------
#
# 1.0 : Initial release
#
# Copyright 2017--2017 Jedrzej Stuczynski. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# try to import modules for python3, if failed, fallback to python2
try:
    import configparser
except ImportError:
    import ConfigParser

import os

from gscholar import get_gscholar_citations
from orcid import get_orcid_citations
from parse_bibtex import clean_up_html
from parse_bibtex import parse_bibtex
from pubmed import get_pubmed_citations


# Todo: reduce file IO and instead pass the objects around

def main():
    try:
        config = configparser.ConfigParser()
    except NameError:
        config = ConfigParser.ConfigParser()

    config.read('config.ini')
    do_orcid = config.get("orcid", "DO_ORCID")
    do_pubmed = config.get("pubmed", "DO_PUBMED")
    do_gscholar = config.get("gscholar", "DO_GSCHOLAR")
    parse_outputs = config.get("bibtex", "PARSE_OUTPUT")

    if not os.path.exists("citations"):
        os.makedirs("citations")

    if do_orcid == "True":
        get_orcid_citations(config)

    if do_pubmed == "True":
        get_pubmed_citations(config)

    if do_gscholar == "True":
        get_gscholar_citations(config)

    if parse_outputs == "True":
        try:
            parse_bibtex(config)
        except IOError:
            return  # no point doing in continuing
        clean_up_html()


if __name__ == '__main__':
    main()
