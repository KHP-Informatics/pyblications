import json
import os
import time
from io import open
from random import randint

from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# todo: handle possible google scholar antibot test


def move_to_element(element, browser_driver):
    """
    Auxiliary method for trying to adjust browser view so that the particular element is visible
    Firstly it tries to use inbuilt move_to_element method.
    If that fails, a javascript script is executed to perform the action.

    :param element: element to move into view
    :param browser_driver: the browser driver
    """

    # moves the window so that the element is visible. This might make it less "suspicious" to gscholar
    action = ActionChains(browser_driver)

    # some browsers drivers seem to have issue in moving to element (such as firefox),
    # so instead we try to move it with javascript
    try:
        action.move_to_element(element).perform()
    except MoveTargetOutOfBoundsException:
        browser_driver.execute_script("arguments[0].scrollIntoView(true);", element)

    time_to_wait = randint(500, 1500)  # in ms
    time.sleep(time_to_wait / 1000.0)


def get_gscholar_citations(config):
    """
    Since Google Scholar does not have any public API and they do not like people automatically scraping their resources,
    we need to "fool" them that the script is a real person so they would not block it.

    For that reason all waiting times are randomly generated so that it would not seem too unhuman.

    The script goes through profiles of each specified person and then pulls bibtex citations for all of their listed publications

    :param config: object representing the configuration file specifying parameters of the job
    """

    scholar_ids = json.loads(config.get("gscholar", "scholar_ids"))

    browser_driver_name = config.get("gscholar", "browser_driver")

    browser_driver = None
    if browser_driver_name == "Edge":
        browser_driver = webdriver.Edge()
    elif browser_driver_name == "Firefox" or browser_driver_name == "Mozilla":
        browser_driver = webdriver.Firefox()
    elif browser_driver_name == "Chrome":
        browser_driver = webdriver.Chrome()

    # THE FOLLOWING WERE NOT TESTED BUT SHOULD WORK
    elif browser_driver_name == "Safari":
        browser_driver = webdriver.Safari()

    if not browser_driver:
        raise ValueError(
            'Incorrect Browser Driver was detected. Check if you have correct name set in the configuration file, alternatively try to reinstall the driver')

    main_window_handle = browser_driver.window_handles[0]

    for keyval in scholar_ids:
        try:
            # this is due to the way the json is structured; each person is represented as an object with single attribute person : scholar id;
            for person, scholar_id in keyval.items():
                print("[Google Scholar] Getting citations for " + person)
                citation_file_name = os.path.join("citations", "".join(person.split()) + "_fromGSCHOLAR.bib")

                citations_url = config.get("gscholar", "BASE_SCHOLAR_URL") + config.get("gscholar",
                                                                                        "SCHOLAR_CITATIONS_URL") + scholar_id + config.get(
                    "gscholar", "SCHOLAR_URL_POSTFIX")

                browser_driver.get(citations_url)

                # waits for page to load (up to 5s)
                try:
                    element_present = EC.presence_of_element_located((By.ID, 'gs_rdy'))
                    WebDriverWait(browser_driver, 5).until(element_present)
                except TimeoutException:
                    print(
                        "Timed out waiting for page to load. Try again later. If the problem persists consider increasing timeout period.")
                    continue

                with open(citation_file_name, "w", encoding="utf-8") as citation_file:
                    # then wait some extra random time
                    time_to_wait = randint(500, 1200)  # in ms
                    time.sleep(time_to_wait / 1000.0)

                    # firstly "reveal" all publications associated with the particular person
                    more_button = browser_driver.find_element_by_xpath(".//*[@id='gsc_bpf_more']")
                    is_more_button_disabled = more_button.get_attribute("disabled")
                    while not is_more_button_disabled:
                        time_to_wait = randint(500, 1500)  # in ms
                        time.sleep(time_to_wait / 1000.0)

                        move_to_element(more_button, browser_driver)

                        # again, some browser drivers throw exception on trying to click disabled button
                        try:
                            more_button.click()
                        except InvalidElementStateException:
                            pass

                        is_more_button_disabled = more_button.get_attribute("disabled")

                    print('Cannot click "Show More" Button anymore. Presumably all results are now loaded')

                    publication_entries = browser_driver.find_elements_by_xpath(".//*[@id='gsc_a_b']/tr/td[1]/a")
                    for idx, entry in enumerate(publication_entries):
                        move_to_element(entry, browser_driver)

                        # gets url for individual publication entry and goes to the page
                        publication_url = entry.get_attribute('href')

                        browser_driver.execute_script("window.open('');")
                        publication_window_handle = browser_driver.window_handles[-1]
                        browser_driver.switch_to.window(publication_window_handle)

                        browser_driver.get(publication_url)
                        try:
                            element_present = EC.presence_of_element_located((By.ID, 'gs_rdy'))
                            WebDriverWait(browser_driver, 5).until(element_present)
                        except TimeoutException:
                            print("Timed out waiting for page to load. Try again later")
                            return

                        # then wait some extra random time
                        time_to_wait = randint(500, 1200)  # in ms
                        time.sleep(time_to_wait / 1000.0)

                        citation_export_handle = browser_driver.find_element_by_xpath(".//*[@id='gsc_btn_exp-bd']")
                        citation_export_handle.click()

                        time_to_wait = randint(500, 800)  # in ms
                        time.sleep(time_to_wait / 1000.0)

                        # goes to the page containing bibtex data and scraps it
                        bibtex_export_button_handle = browser_driver.find_element_by_xpath(
                            ".//*[@id='gsc_btn_exp-md']/ul/li[1]")
                        bibtex_export_button_handle.click()

                        WebDriverWait(browser_driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "pre"))
                        )

                        citation = browser_driver.find_element_by_tag_name('pre').text

                        time_to_wait = randint(500, 1200)  # in ms
                        time.sleep(time_to_wait / 1000.0)

                        citation_file.write(citation + "\n")

                        print("Current citation: " + str(idx + 1) + " for " + person)

                        browser_driver.close()
                        browser_driver.switch_to.window(main_window_handle)
                        time_to_wait = randint(400, 1200)  # in ms
                        time.sleep(time_to_wait / 1000.0)

        # if procedure is forcefully terminated, make sure to close the browser
        except KeyboardInterrupt:
            browser_driver.close()

    browser_driver.close()
