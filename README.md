# Academic Publications List Generator
These scripts are designed to compile list of academic publications of specified people by using resources available on the web.

Currently it supports getting publications that are already listed on:
- Orcid (https://orcid.org)
- PubMed (https://www.ncbi.nlm.nih.gov)
- Google Scholar (https://scholar.google.co.uk)

## Installation

First and foremost, in order to use the scripts, you require a python installation to be present on your system.
It can be downloaded from https://www.python.org/downloads/ . Please mind that although the scripts should work with both python 2.7 and python 3, installing python 3 is recommended.

Furthermore, they heavily depend on third-party modules being present and the following need to be done:

1. Install **pybtex** (helps to manage and parse bibtex citations)
```
pip install pybtex
```

2. Install **lxml** (helps in parsing XML documents). Usually it comes with the python distribution, but in case it doesn't run the following:
```
pip install lxml
```

3. Install **selenium** (used to mimic people behaviour in a web browser; used for getting Google Scholar citations):
```
pip install selenium
```

4. In order to use selenium, you will need a webdriver for a browser of your choice. Get it from one of:
- Firefox: https://github.com/mozilla/geckodriver/

- Chrome: https://sites.google.com/a/chromium.org/chromedriver/

- Edge: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

- Safari (not tested): https://github.com/SeleniumHQ/selenium/wiki/SafariDriver

Then follow the installation instructions provided.

5. You will also require an installation of LaTeX to be present on your system. The scripts were tested to be working correctly with:
- TexLive on Ubuntu 16.04
- MikTex on Windows 10

-- Installation guide for TexLive (Windows and Unix): https://www.tug.org/texlive/ 

-- Installation guide for MikTex (Windows and OSX (*not tested*)): https://miktex.org/download

However, the specific implementation should not make a significant difference on the final result.

## Usage
The scripts were adjusted to be compatible with both versions of python, i.e python 2.7 and python 3. 
However, using python 3 is recommended.

Furthermore, scripts were tested to run correctly in Windows and Linux environments. 
However, Mac version was not tested, so if you happen to use this environment, please let me know of the results.

Running the script is as simple as executing the following commands from within the directory:
```
python main.py
```

Keep in mind, while the results from Orcid and PubMed will be gathered behind the screen, within few seconds, 
quering Google Scholar will take considerably more time and will be literally on the screen. 
Your selected browser is going to simulate your behaviour in order to obtain the citations.
Please do not close it while it is running. It will close itself when it is done.

However, as you will notice, this command did not produce anything useful and did not let you specify whose citations you wish to obtain. 
That is because those settings are kept in a configuration file, `config.ini`, which you need to modify first.

It is divided into sections, each responsible for a particular feature.

### Important settings:

#### orcid

-`DO_ORCID` - decides whether Orcid resources should be queried. Set it to *True* to run it, *False* otherwise.

-`ids_to_check` - represents list of ids of people whose ids should be checked in order to get their citations. It follows JSON-like syntax.
Example:
```
ids_to_check = [
    {"Lorem Ipsum" : "1234-5678-9012-3456"},
    {"Dolor Sit" : "1234-5678-9012-3456"},
    {"Consectetur Adipiscing" : "1234-5678-9012-3456"}
    ]
```


#### pubmed

-`DO_PUBMED` - decides whether PubMed should be queried. Set it to *True* to run it, *False* otherwise.

-`people_to_check` - represents list of people whose publications should be found. Each person is represented as "FirstName, LastName".
Example:
```
people_to_check = [
    "Lorem Ipsum",
    "Dolor Sit",
    "Consectetur Adipiscing"
    ]
```

#### gscholar
-`DO_GSCHOLAR` - decides whether Google Scholar should be queried. Set it to *True* to run it, *False* otherwise.

-`browser_driver` - specifies which browser the scripts should use (make sure you have installed the driver for it). 
Current options include: "Chrome", "Edge", "Firefox", "Safari" (untested)

-- `scholar_ids` - represents list of ids of people whose ids should be checked in order to get their citations. It follows JSON-like syntax.
Example:
```
scholar_ids = [
    {"Alan Turing" : "f8HQJLAAAAA"},
    {"Lorem Ipsum" : "ABCDEFGHIJK"},
    {"Dolor Sit" : "LMNOPRSTUVQ"}
    ]
```

#### bibtex
-`PARSE_OUTPUT` - decides whether the outputs from previous steps should be combined and parsed. Set it to *True* to enable it, *False* otherwise.

-`citation_style_file` - name of the file defining the style of your citations. Two sample ones are attached: apa and chicago. However, you may use your own.

-`output_directory` - location for your output HTML files.
