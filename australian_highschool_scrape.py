import csv
import multiprocessing
import os
import re
import time
import timeit

import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent
from selenium import webdriver
from unidecode import unidecode

# dynamic pathname based on different device, instead of hard coding the pathname
uniqueLinkList_path = os.path.join(os.getcwd(), 'UniqueLinkList_.csv')
extractedData_path = os.path.join(os.getcwd(), 'ExtractedData.csv')

# Setup Chrome display
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")

#  Change according to the homepage of the site
Homepage = 'https://www.goodschools.com.au'

user = UserAgent().random
headers = {'User-Agent': user}

def collect_school_links(str_link):
    options.add_argument(f'user-agent={user}')
    options.add_argument('--disable-gpu')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options, executable_path=r'C:\Users\Nicholas\Documents\Summer intern @ Seeka\chromedriver.exe')
    driver.get(str_link)  # This will open the page using the URL
    #content = driver.page_source.encode('utf-8').strip()
    #page = requests.get(str_link, timeout=10, headers=headers)
    #soup = BeautifulSoup(page.text, "lxml")

    driver.find_element_by_link_text('»').click()

    while True:

        soup = BeautifulSoup(driver.page_source, 'lxml')
        for a in soup.find_all('div', class_='row row-padding-10'):
            for x in a.find_all('div', class_='col-md-12 clear-fix'):
                b = x.find('a')
                print(b['href'])

        try:
            driver.find_element_by_link_text('»').click()
            print("Clicked on the next page")
            continue
        except:
            break


collect_school_links("https://www.goodschools.com.au/compare-schools/search?state=ACT")