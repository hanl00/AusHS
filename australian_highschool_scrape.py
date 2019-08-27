import csv
import multiprocessing
import os
import re
import time
import timeit

import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from fake_useragent import UserAgent
from selenium import webdriver
from unidecode import unidecode

# dynamic pathname based on different device, instead of hard coding the pathname
uniqueLinkList_path = os.path.join(os.getcwd(), 'UniqueLinkList.csv')
extractedData_path = os.path.join(os.getcwd(), 'ExtractedData.csv')

# Setup Chrome display
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")

#  Change according to the homepage of the site
Homepage = 'https://www.goodschools.com.au'

user = UserAgent().random
headers = {'User-Agent': user}

#obtaining links for all the institutions by region
def collect_institution_links(str_link):

    with open(uniqueLinkList_path, 'wt',encoding='utf-8', newline='') as Linklist:
        writer2 = csv.writer(Linklist)
        options.add_argument(f'user-agent={user}')
        options.add_argument('--disable-gpu')
        # options.add_argument('--headless')
        driver = webdriver.Chrome(options=options, executable_path=r'C:\Users\Nicholas\Documents\Summer intern @ Seeka\chromedriver.exe')
        driver.get(str_link)  # This will open the page using the URL

    #content = driver.page_source.encode('utf-8').strip()
    #page = requests.get(str_link, timeout=10, headers=headers)
    #soup = BeautifulSoup(page.text, "lxml")

        total_link_info = ['']

        while True:

            soup = BeautifulSoup(driver.page_source, 'lxml')
            for a in soup.find_all('div', class_='row row-padding-10'):
                for x in a.find_all('div', class_='col-md-12 clear-fix'):
                    b = x.find('a')
                    print(b['href'])
                    institution_link = Homepage + b['href']
                    total_link_info[0] = institution_link
                    writer2.writerow(total_link_info)
                    time.sleep(1)
            try:
                driver.find_element_by_link_text('»').click()
                print("Clicked on the next page")
                continue
            except:
                break


#multiprocessing structure
def multi_pool(func, input_name_list, procs):
    templist = []
    # counter = len(input_name_list)
    pool = multiprocessing.Pool(processes=procs)
    # print('Total number of processes: ' + str(procs))
    for a in pool.imap(func, input_name_list):
        templist.append(a)
        # print('Number of links left: ' + str(counter - len(templist)))
    pool.terminate()
    pool.join()
    return templist


#retrieving all relevant information from the institution's profile page
def collect_institution_data(str_institution_link):

    #array structure = [ PRINCIPLE NAME,
    complete_school_details = ['']
    options.add_argument(f'user-agent={user}')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options, executable_path=r'C:\Users\Nicholas\Documents\Summer intern @ Seeka\chromedriver.exe')
    driver.get(str_institution_link)  # This will open the page using the URL
    soup = BeautifulSoup(driver.page_source, 'lxml')
    x = soup.find('div', class_='box border-grey')
    for contents in x:
        try:
            print(contents.get_text())
        except NavigableString:
            pass


collect_institution_data("https://www.goodschools.com.au/compare-schools/in-Deakin-2600/alfred-deakin-high-school")