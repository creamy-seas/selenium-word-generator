#!/usr/bin/env python
# coding: utf-8

# # Import package

# In[1]:


import time
# create a browser instance
from selenium import webdriver
# emulate keyboard inputs
from selenium.webdriver.common.keys import Keys
# creatinga single browser instance
import selenium.webdriver.firefox.service as service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
# WebDriverWait and EC to allow waiting for element to load on page
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# module to search for elements using xpaths
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
# exception handling
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# quick clicking and scrolling
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# searching of html with "find()"
from bs4 import BeautifulSoup
import pandas as pd
import sys
import math
import os                       # file saving
import datetime
import re
import unidecode                # to remove accents
import random


# # Selenium Bot Class

# ### Make sure that "chromedriver" and "geckodriver" are in this directory

# In[2]:


class selenium_bot():
    """
    Interactable bot, that parses outlook files
    """

    def __init__(self, browser, timeout, save_period, url, page_loaded_xpath):
        """
        __ Parameters __
        [str] browser: "Firefox" or "Chrome"
        [float] timeout: how long to wait for responses
        [save_period] float: time in seconds to create backup of parsed data
        [str] url: url bot starts off at
        [str] page_loaded_xpath: xpath to indicate that page has loaded

        __ Description __
        sets up selenium bot
        """

        self.browser = browser.lower()
        self.timeout = timeout
        self.url = url
        self.page_loaded_xpath = page_loaded_xpath

        # 1 - setup browser
        print("==> setup_browser start")
        if(self.browser == "firefox"):
            self.driver = self.__setup_firefox()
        else:
            self.driver = self.__setup_chrome()
        self.driver.maximize_window()

        # 2 - load page
        self.driver.get(self.url)

        # 3- supprorting parameters for the future
        # waiter, to wait for contents to load. call the "waiter.until(function)" method
        self.WebDriverWaiter = WebDriverWait(self.driver, self.timeout)
        self.save_period = save_period

        print("==> setup_browser end\n")

    def __setup_firefox(self):
        """
        __ Description __
        open up a firefox driver

        __ Returns __
        driver handle
        """

        # 1 - create a browser instance
        print("  > Starting new Firefox server")
        browser = webdriver.Firefox(
            executable_path='./geckodriver')

        return browser

    def __setup_chrome(self):
        """
        __ Description __
        open up a chrome driver

        __ Returns __
        driver handle
        """

        # 1 - set capabilities
        capabilities = {'chromeOptions':
                        {
                            'useAutomationExtension': False,
                            'args': ['--disable-extensions']}
                        }

        # 2 - set options for chrome
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        # 3 - create a browser instance with defined options
        print("  > Starting new Chrome server")
        browser = webdriver.Chrome(executable_path="./chromedriver",
                                   desired_capabilities=capabilities,
                                   options=chrome_options)
        return browser

    def supp_extract_html(self, soup, html_tags_array):
        """
        __ Parameters __
        [soup] soup: html to extract from formatted with BeautifulSoup
        html_tags_array: array of the form

        [["div", {"role": "option"}], 
        ["div", {"aria-label": "Reading Pane"}], 
        ...]

        which specifies the name ("div", "span") and attributes ({"id": ["test1", "test2"], "aria-label": "pane"})
        from outer to inner tags, iteratively going down specificity levels

        __ Description __
        iterates through the supplied "soup" html looking for tags whose parrents match all the supplied "html_tags"

        __ Return __
        [htmltag1, htmltag2, htmltag3]: array of html tags that fit the search requirement
        """

        structure_depth = len(html_tags_array)
        debug_counter = 0

        try:
            if(structure_depth != 1):
                # 1 - unpack the first structure
                current_structure = soup.find(
                    html_tags_array[0][0], attrs=html_tags_array[0][1])

                # 2 - unpack further structures until we get to the last one
                for i in range(1, structure_depth - 1):
                    debug_counter += 1
                    name = html_tags_array[i][0]
                    attrs = html_tags_array[i][1]
                    current_structure = current_structure.find(
                        names, attrs=attrs)

                # 3 - extract all matches from the lowest structure
                current_structure = current_structure.find_all(
                    html_tags_array[-1][0], attrs=html_tags_array[-1][1])
            else:
                # 1 - in the special case that only one structure is specified
                current_structure = soup.find_all(
                    html_tags_array[0][0], attrs=html_tags_array[0][1])

            return current_structure

        except AttributeError:
            # Error when an entry is missing
            print("The page does not have the html element:\n\t[%s, %s]"
                  % (html_tags_array[debug_counter], html_tags_array[debug_counter]))

            return ""

    def supp_extract_text(self, soup, html_tags_array):
        """
        __ Parameters __
        [soup] soup: html to extract from formatted with BeautifulSoup
        html_tags_array: array of the form

        [["div", {"role": "option"}], 
        ["div", {"aria-label": "Reading Pane"}], 
        ...]

        which specifies the name ("div", "span") and attributes ({"id": ["test1", "test2"], "aria-label": "pane"})
        from outer to inner tags, iteratively going down specificity levels

        __ Description __
        iterates through the supplied "soup" html looking for tags whose parrents match all the supplied "html_tags"
        then a text array is extracted from this tag

        __ Return __
        [array] matching text in the innter structure
        """

        html_structure = self.supp_extract_html(soup, html_tags_array)

        # 1 - take all of the tags found and extract text
        array_to_return = [i.get_text().strip() for i in html_structure]

        return array_to_return

    def supp_write_to_element(self, element_xpath, fill_value):
        """
        __ Parameters __
        [str] element_xpath: element to look for e.g. //div[@id=|password|]
        [str] fill_value: what to write in the form

        __ Description __
        enters the "fill_value" into the chosen "element"
        """
        self.supp_wait_for_xpath(element_xpath)

        element = self.driver.find_element_by_xpath(element_xpath)
        if(element):
            element.send_keys(fill_value)
        else:
            print("**> Element with xpath %s does not exist" % element_xpath)

        return True

    def supp_wait_for_xpath(self, xpath):
        """
        __ Parameters __
        [str] xpath: xpath to wait for

        __ Description __
        pauses the browser until "xpath" is loaded on the page
        """
        self.WebDriverWaiter.until(
            EC.presence_of_element_located(
                (By.XPATH, xpath)),
            message="Did not find %s within the timeout time you set of %i" % (
                xpath, self.timeout)
        )

    def supp_click(self, xpath):
        """
        __ Parameters __
        [str] xpath: xpath of object to click

        __ Description __
        clicks the element
        """
        self.driver.find_element_by_xpath(xpath).click()

    def supp_load_soup(self):
        """
        Loads up a soup of all the html on the visible page
        __ Returns __
        Soup Object to search
        """
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        return soup

    def refresh(self):
        """
        __ Description __
        Resets variables of bot class and reload page
        """
        self.pandas_out = pd.DataFrame(columns=self.pandas_out.columns)
        running_class.driver.get(self.url)
        self.supp_wait_for_xpath(self.page_loaded_xpath)

    def supp_save_data(self, file_name="pandas_out", ext="csv"):
        """
        __ Parameters __
        [str] file_name: the file to save to. provide .pkl or .csv extension

        __ Description __
        Saves data accumulated in "pandas_out" to output file
        """

        # 1 - create output directory
        if not os.path.exists("./output"):
            os.mkdir("output")

        # 2 - cut any extensions that were given by accident
        file_name = file_name.split(".")[0]
        file_name = "./output/%s" % (file_name)

        if(ext == "pkl"):
            self.pandas_out.to_pickle("%s.pkl" % file_name)
        else:
            self.pandas_out.to_csv("%s.csv" % file_name)


# # Data generator

# In[80]:


def wikipedia_scrape_words():
    # 1 click random article
    running.driver.find_element_by_xpath("//li[@id = 'n-randompage']").click()

    # 2 exract all text
    soup = running.supp_load_soup()
    page_title = soup.find("h1", attrs={"id": "firstHeading"}).get_text()
    page_content = soup.find(
        "div", attrs={"class": "mw-content-ltr"}).get_text()
    page_text = page_content.split(" ")

    # 3 -filter only words with characters a-z and before refferences
    page_text_filtered = set()
    for i in page_text:

        # do not look at beyond refferences
        mg_refference = re.search(".*References\\[edit\\].*", i, flags=re.S)
        if(mg_refference):
            break

        # do not keep words with capitalized letters inthe middle or numbers
        mg_Capital = re.findall("(\s|^)((\w+[A-Z]\w+)|(.*\d.*))(\s|$)", i)
        if(mg_Capital):
            pass
        else:
            # search for full words of length 2-15 and exclude square brackets
            mg = re.search("(\s|^)(\w{2,15})(\\[\d+\\])?(\s|$)", i)
            if(mg):
                filtered = mg.group(2).lower()
                page_text_filtered.add(filtered)

    return set(page_text_filtered), page_title


def convert_to_nn_format(set_to_convert):
    """
    __ Parameters __
    set_to_convert

    __ Description __
    converts the supplied set by
    - trimming to 15 characters
    - removing all accents
    - lowercasing


    __ Return __
    converted_set, number_of_deletions
    """
    converted_set = []

    for i in set_to_convert:
        # only words 2-15 kept
        mg = re.search("(\w{2,15})", i)
        if(mg):
            # lower case
            i = i.lower()

            # remove accents
            i = unidecode.unidecode(i)

            converted_set.append(i)

    return set(converted_set)


class wait_for_change():
    """Wait for the content of the specified locator to change

    To be used in the following way:
    formWebDriverWait.until(wait_for_content_loaded())
    """

    def __init__(self, locator, old_value):
        self.locator = locator
        self.old_value = old_value

    def __call__(self, driver):

        try:
            present = EC._find_element(driver, self.locator).text.strip()
            present_changed = ((present != "") and (present != self.old_value))

            return present_changed

        except StaleElementReferenceException:
            return False


def write_set(set_to_write, name):
    """
    __ Parameters __
    [str] name: name of output file
    [set] set_to_write: set to write to file

    __ Description __
    write to file in format
    word, unique id
    """

    fout = open(name, "a")
    set_list = list(set_to_write)[:10000]

    for i in set_list:
        unique_id = random.randrange(1**10, 9 * 10**10)
        to_write = "%s, %i\n" % (i, unique_id)
        fout.write(to_write)

    fout.close()
    print("==> Wrote set to file %s.txt" % (name))


# ## Browser instance

# In[18]:


########################################
########################################
# seconds to wait for page elements to load before quitting
timeout = 100
browser = "chrome"                # firefox of chrome
url = "https://en.wikipedia.org/wiki/Main_Page"
########################################
########################################
running = selenium_bot(browser, timeout, None, url, None)


# ## Chinese set

# In[ ]:
english_file_to_use = "./output/english_chinese1.txt"
# page slows down after a few traslations, so food to reload it
no_sections_to_split_into = 100


# 1 - set to translate from english to chinese
running.driver.get("https://translate.google.com/")
running.supp_click("//div[@class='sl-wrap']/div/div[2]/div[@value='en']")
running.supp_click("//div[@class='tl-wrap']/div[@aria-label='More']")
try:
    running.supp_click(
        "//div[@class='language_list_item_wrapper language_list_item_wrapper-zh-TW']")
except:
    pass

# 2 - load up file with english words (generated above)
english_for_chinese_set = []
with open(english_file_to_use, "r") as fin:
    for line in fin:
        english_for_chinese_set.append(line.split(",")[0])


# 3 - split the word up into sections
length_english_set = len(english_for_chinese_set)
section_length = int(length_english_set / no_sections_to_split_into)
print("==> Transalting English. Using %i sections x %i words each for a total of %i words" %
      (no_sections_to_split_into, section_length, no_sections_to_split_into * section_length))


for section in range(10, no_sections_to_split_into):

    # a - set section variables
    begin = section * section_length
    end = (section + 1) * section_length
    english_set_section = list(english_for_chinese_set)[begin:end]
    translation_old = ""
    chinese_set = set()

    for i, english_word in enumerate(english_set_section):
        # b - write word to translate
        running.supp_write_to_element("//textarea", english_word)

        # c - wait for translation to load
        running.WebDriverWaiter.until(wait_for_change((By.XPATH,
                                                       "//div[@class='tlid-result-transliteration-container result-transliteration-container transliteration-container']"), translation_old))

        # d - extract translation
        translation = running.supp_extract_text(running.supp_load_soup(),
                                                [["div",
                                                  {"class": "tlid-result-transliteration-container result-transliteration-container transliteration-container"}],
                                                 ["div",
                                                  {"class": "tlid-transliteration-content transliteration-content full"}]])
        translation = "".join(translation)
        translation_old = translation

        # e - ensure that word was translated
        if(translation.lower() != english_word):

            # f - if there is more than 1 word in the output, choose a random one
            translation = translation.split(" ")
            length_translation = len(translation)
            if(length_translation == 1):
                translation = translation[0]
            else:
                translation = translation[random.randrange(
                    0, length_translation)]

            print("%i\t%s\t\t|%s" % (i, english_word, translation.strip()))
            chinese_set.add(translation.strip())

        else:
            print("Word \"%s\" skipped" % english_word)

        # e - clear the input field before rerunning
        running.driver.find_element_by_xpath("//textarea").clear()

    # 2 - tidy the words and write to file
    print("-------------------- Section %i/%i--------------------" %
          (section, no_sections_to_split_into))
    chinese_set = convert_to_nn_format(chinese_set)
    write_set(chinese_set, "./output/chinese.txt")

    # 3 - reload page to clear cache
    running.driver.get("https://translate.google.com/")


print("==> Translated %i English words to %i Chinese words" %
      (len(english_for_chinese_set), len(chinese_set)))
