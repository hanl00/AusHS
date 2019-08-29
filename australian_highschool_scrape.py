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


# obtaining links for all the institutions by region
def collect_institution_links(str_link):
    with open(uniqueLinkList_path, 'wt', encoding='utf-8', newline='') as Linklist:
        writer2 = csv.writer(Linklist)
        options.add_argument(f'user-agent={user}')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options,
                                  executable_path=r'C:\Users\Nicholas\Documents\Summer intern @ Seeka\chromedriver.exe')

        driver.get(str_link)
        total_link_info = ['']

        while True:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            for a in soup.find_all('div', class_='row row-padding-10'):
                for x in a.find_all('div', class_='col-md-12 clear-fix'):
                    b = x.find('a')
                    institution_link = Homepage + b['href']
                    total_link_info[0] = institution_link
                    writer2.writerow(total_link_info)
                    time.sleep(1)
            try:
                driver.find_element_by_link_text('»').click()
                print("Moving on to the next page")
                continue
            except:
                print("This is the last page")
                break


# multiprocessing structure
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


multiple_profiles = []


# retrieving all relevant information from the institution's profile page
def collect_institution_data(str_institution_link):
    complete_school_details = {}
    global multiple_profiles
    page = requests.get(str_institution_link)
    soup = BeautifulSoup(page.content, 'lxml')

    # begin by getting institution name and region
    header_texts = soup.find('div', class_='school-details').find('div', class_='header').get_text()
    str_list = header_texts.split("\n")
    cleaned_h_texts = list(filter(None, str_list))
    complete_school_details['Institution Name'] = cleaned_h_texts[0].lstrip().rstrip()
    complete_school_details['Institution Region'] = cleaned_h_texts[1].lstrip().rstrip()

    # proceed to obtain data from the top right box
    # - Sector, Government, Gender, Religion (found in some listings)
    for p_tags in soup.find('div', class_='box-content box-section-padding').findAll('p'):
        cleaned_text = p_tags.getText().replace(" ", "").replace("\n", "")
        sorted_text = re.findall('([A-Z][a-z]*)', cleaned_text)
        complete_school_details[sorted_text[0]] = sorted_text[1]

    # obtaining data from the right mid box
    # - Principal, Addresses, Tel, Links to school's website
    for p_tags in soup.find('div', class_='box border-grey').findAll('p'):
        links = p_tags.findAll('a')
        for a in links:
            if a.getText() == "Visit school's website":
                complete_school_details["Visit school's website"] = a['href']

        cleaned_text = p_tags.getText().replace("\n", "")
        sorted_text = cleaned_text.split(":")
        if len(sorted_text) == 2:
            complete_school_details[sorted_text[0].lstrip().rstrip()] = sorted_text[1].lstrip().rstrip()

    #  check if school has multiple profiles
    #  - https://www.goodschools.com.au/compare-schools/in-Hawthorn-3122/scotch-college-hawthorn/boarding
    if "School Profile" in complete_school_details.keys():
        print(complete_school_details['Institution Name'] + " has multiple profiles")
        multiple_profiles.append(complete_school_details['Institution Name'])
        del complete_school_details['School Profile']
    print(complete_school_details)


if __name__ == '__main__':
    # collect_institution_links("https://www.goodschools.com.au/compare-schools/search?state=NT")
    collect_institution_data("https://www.goodschools.com.au/compare-schools/in-Hawthorn-3122/scotch-college-hawthorn/boarding")

    if len(multiple_profiles):
        print("These are the institutions with multiple profiles " + str(multiple_profiles))
