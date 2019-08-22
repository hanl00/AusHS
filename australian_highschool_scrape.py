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
Homepage = 'https://www.tripadvisor.com.my'

user = UserAgent().random
headers = {'User-Agent': user}

# import methods from previous version of code
class Methods:
    # Check if the variable data type is None
    def CheckNone(link):
        if link != None:
            return True
        else:
            return False

    # Check if the passed string contains http or https
    def HttpCheck(link):
        if Methods.CheckNone(link):
            if ('https://' in link) or ('http://' in link):
                return True
            else:
                return False
        else:
            return False

    # Check if link is Unique
    def Unique(link):
        with open(uniqueLinkList_path, 'rt',
                  encoding='utf-8') as Linklist:
            reader = csv.reader(Linklist)
            for url in reader:
                # print(url)
                if Methods.CheckNone(link) & Methods.CheckNone(url[3]):
                    if link == str(url[3]).replace('[', '').replace("'", '').replace(']', ''):
                        Linklist.close()
                        return False
                else:
                    Linklist.close()
                    return False
            return True

def get_text_with_br(tag, result=''):
    for x in tag.contents:
        if isinstance(x, Tag):  # check if content is a tag
            if x.name == 'br':  # if tag is <br> append it as string
                result += str(x)
            else:  # for any other tag, recurse
                result = get_text_with_br(x, result)
        else:  # if content is NavigableString (string), append
            result += x

    return result


def collect_links(link, category, country, city, process_num):

    with open(uniqueLinkList_path, 'at',encoding='utf-8', newline='') as Linklist:
        writer2 = csv.writer(Linklist)
        options.add_argument(f'user-agent={user}')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        driver = webdriver.Chrome(chrome_options=options, executable_path=r'C:\Users\Nicholas\Documents\Summer intern @ Seeka\chromedriver.exe')
        driver.get(str(link))  # This will open the page using the URL
        content = driver.page_source.encode('utf-8').strip()
        # driver_soup = BeautifulSoup(content, "html.parser")

        page = requests.get(link, timeout=10, headers=headers)
        soup = BeautifulSoup(page.text, "lxml")

        # req = requests.get(str(link), headers=headers)
        # reqsoup = BeautifulSoup(req.content, 'lxml')

        key_url_list = []
        total_link_info = ['', '', '', '']
        # Get all the activity links

        num = 0
        # we only want to click on the "limit search" once for smaller cities,
        #   clicking more than once will result in an endless loop in some pages

        counter_limit_search = 0

        while True:
            time.sleep(2)
            try:
                driver.find_element_by_class_name('ui_tab_bar').find_elements_by_css_selector('li')[1].click()
                print("Locating ui_tab_bar for url " + driver.current_url)
            except:
                print("Error locating ui_tab_bar for url " + driver.current_url)
                pass

            # check for the "Limit search to X" button
            # note: this button appears when the city has few activities or the "outdoor activities" and "tours" page
            try:
                if counter_limit_search < 1:
                    driver.find_element_by_id("secondaryText").click()
                    print("Limiting search within " + 'city_of_country' + " for url " + driver.current_url)
                    # allow website to update itself
                    time.sleep(5)
                    counter_limit_search += 1

            # pass ElementNotVisibleException
            except:
                print("Limit search button not visible for url " + driver.current_url)
                pass

            test_soup = BeautifulSoup(driver.page_source, 'lxml')

            for link_test in test_soup.find_all('div', {'class': 'listing_title title_with_snippets'}):
                for href in link_test.find_all('a'):
                    activity_link = Homepage + href.get('href')
                    if Methods.CheckNone(activity_link):
                        if Methods.HttpCheck(activity_link) & Methods.Unique(activity_link):
                            u = (str(activity_link).split('\n'))
                            total_link_info[0] = category
                            total_link_info[1] = country
                            total_link_info[2] = city
                            total_link_info[3] = str(u).replace("[", "").replace("]", "").replace("'", "")
                            time.sleep(1)
                            if len(total_link_info) == 4:
                                writer2.writerow(total_link_info)
                                time.sleep(1)
                                key_url_list.append(activity_link)
                                num += 1

        # Clicking on the Next Page
            try:
                if 'Next' in driver.find_element_by_class_name("disabled").text:
                    raise Exception
                else:
                    currentlink = driver.current_url
                    driver.find_element_by_class_name("next").click()
                    time.sleep(5)
                    nextlink = driver.current_url
                    if currentlink == nextlink:
                        driver.find_element_by_link_text("3").click()
                        time.sleep(2)
                        driver.find_element_by_class_name("previous").click()
                        time.sleep(2)
                    continue
            except:
                break


    print("================================\nAll " + str(num) + " the links have been collected")
    print("Link collected: " + str(key_url_list))

def collect_data(category, country, city, attraction_list, process_num):

    with open(extractedData_path, 'at', encoding="utf-8", newline='') as website:
        writer = csv.writer(website)

        num_loop = 0
        finished = 0
        retry_count = 0
        response = requests.get(str(attraction_list), headers=headers, timeout=10)  # finds a response from the link to see if it's working
        soup = BeautifulSoup(response.content, "lxml")

        while True:
            while finished != 1:

                if soup.find_all("div", {'class': 'errHdr'}):
                    print('Skipping...' + attraction_list + 'link is empty - error 404. ')
                    break

                elif soup.find_all('div', {'class': 'attractions-price-block-FromPriceBlock__mainPrice--2XwLZ'}):
                    print('Skipping...' + attraction_list + '. Not an attraction. ')
                    break

                try:
                    if retry_count == 5:  # If except: No connection, up to 5 times then loop will break
                        print('This link cannot be opened ' + attraction_list)
                        num_loop += 1
                        break
                    else:
                        time.sleep(1)  # buffer period
                        print('OPENING ' + attraction_list)
                        if response:
                            finished = 1
                except requests.exceptions.ConnectionError as e:  # Multi Pool does not work without defining this
                    print(e)
                    print('No connection, Retrying...' + attraction_list)
                    retry_count += 1
                    continue
                except requests.exceptions.ReadTimeout as e:
                    print(e)
                    print('Timeout Error.  ' + attraction_list)
                    retry_count += 1
                    continue

            else:
                details = ['', '', '', '', '', '', '']
                # Name || from 3 layouts of TripAdvisor
                for a in soup.find_all('div', {'id': 'photo-and-header-product-title'}):
                    for b in a.find_all('h1', {'class': 'ui_header h1 attractions-product-info-ProductTitle__title--1qM0o'}):
                        b = b.get_text()
                        b = unidecode(b)
                        details[0] = b.title()

                if details[0] == '':
                    for a in soup.find_all('div', {'id': 'taplc_attraction_company_details_acr_responsive_0'}):
                        for b in a.find_all('h1', {'id': 'HEADING'}):
                            b = b.get_text()
                            b = unidecode(b)
                            details[0] = b.title()

                if details[0] == '':
                    for a in soup.find_all('div', {'class': 'attractionsHeader'}):
                        for b in a.find_all('h1', {'id': 'HEADING'}):
                            b = b.get_text()
                            b = unidecode(b)
                            details[0] = b.title()

                # Category of the Attraction.
                details[1] = category

                # City Name
                # if soup.find('div', {'class': 'global-nav-links-container'}) is not None:
                #     navigation_container = soup.find('div', {'class': 'global-nav-links-container'}).find(
                #         'li').find('span')
                #     city_text = navigation_container.get_text()
                #     city_text = " ".join(city_text.split())
                # details[1] = city_text
                details[2] = city

                # Country Name
                # if soup.find('div', {'class': 'attractionsBLInfo'}) is not None:
                #     country_text = soup.find('div', {'class': 'attractionsBLInfo'}).find('span', {
                #         'class': 'country-name'}).get_text()
                #     details[3] = country_text

                details[3] = country

                # Location || from 3 layouts of TripAdvisor
                location = ''
                for a in soup.find_all('ul', {'class': 'list'}):
                    for b in a.find_all('li', {'class': 'pois'}):
                        for c in b.find_all('span', {'class': 'poi_links'}):
                            for d in c.find_all('a'):
                                if 'and' not in d.get_text():
                                    location = location + d.get_text() + ', '
                                else:
                                    location = location + d.get_text()

                details[4] = location

                if details[4] == '':
                    for a in soup.find_all('div',
                                           {
                                               'class': 'attractions-contact-card-ContactCard__contactRow--3Ih6v'}):
                        details[4] = a.get_text()

                if details[4] == '':
                    for a in soup.find_all('div', {'class': 'address'}):
                        for b in a.find_all('span', {'class': 'detail'}):
                            details[4] = b.get_text()

                # Overview || from 3 layouts of TripAdvisor
                for a in soup.find_all('div',
                                       {'class': 'attractions-product-details-Overview__textWrapper--1fTL6'}):
                    for b in a.find_all('span'):
                        c = get_text_with_br(b)
                        c = c.replace('<br>', ' ')
                        c = c.replace('\n', '').replace('\t', '')
                        c = unidecode(c)
                        c = c.replace('...more', ' ').replace('Read more', ' ')
                        details[5] = c

                if details[5] == '':
                    for a in soup.find_all('div',
                                           {'class': 'attractions-supplier-profile-SupplierAbout__about--1HdOk'}):
                        for b in a.find_all('div', {'class': 'attractions-supplier-profile-SupplierDescription__description--lzIK9'}):
                            c = get_text_with_br(b)
                            c = c.replace('<br>', ' ').replace('<br/>', ' ')
                            c = c.replace('\n', '').replace('\t', '')
                            c = unidecode(c)
                            c = c.replace('...more', ' ').replace('Read more', ' ')
                            details[5] = c

                if details[5] == '':
                    for a in soup.find_all('div', {'class', 'ppr_rup ppr_priv_location_detail_about_card'}):
                        # print(a)
                        c = get_text_with_br(a)
                        c = c.replace('<br>', ' ').replace('<br/>', ' ').replace('About', '')
                        c = c.replace('\n', '').replace('\t', '')
                        c = unidecode(c)
                        c = c.replace('...more', ' ').replace('Read more', ' ')
                        if 'UndergroundF' in c:
                            c = c.split('Fdeg')[0]
                            if 'Local WeatherPowered by  Weather Underground' == c:
                                details[5] = ''
                            else:
                                details[5] = c.replace('Local WeatherPowered by  Weather Underground', '')
                        else:
                            details[5] = c

                # URL Link of the Attraction page.
                try:
                    details[6] = response.url  # Gets URL of the link
                except:
                    continue

                print(details)
                writer.writerow(details)  # Writes data in csv file
                # print('Adding item no.' + str(num_loop) + ' to list')
                # print(details)
                num_loop += 1
                time.sleep(3)
            # print("\n" + str(len(attraction_list)) + " in the queue of " + '' + city + '')
            break


# end of import from previous code


def parsing_script_input(line):
    line_split = line.split(',')
    string_1, string_2, string_3 = line_split[0], line_split[1], line_split[2]
    return string_1, string_2, string_3


# input: user provided TripAdvisor url
# output: dictionary containing key = category type; value = category type url
def collect_category_link(url):

    dictionary_category_link = {}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "lxml")

    try :
    # look for the FIRST container - types of things to do; use "find" not "findall"; this also takes care of the occurence of the "see all" button
        types_of_things_todo = soup.find(class_='attractions-attraction-overview-pills-PillShelf__pillShelf--3uaz2')

        for link in types_of_things_todo.find_all('a', href=True):
            key = re.sub(r" ?\([^)]+\)", "", link.text)
            value = Homepage + link['href']
            dictionary_category_link[key] = value
    except:
        print("Unsupported page format for " + url)
        unsupported_links.append(url)
        pass

    return dictionary_category_link


def main():

    start = timeit.default_timer()

    global unsupported_links
    unsupported_links = []

    with open(uniqueLinkList_path, 'wt') as Linklist:
        Linklist.close()

    # activity_url_list = [], if global have to collect all url links for every city in the country

    with open(extractedData_path, 'wt', encoding="utf-8", newline='') as website:
        writer = csv.writer(website)
        writer.writerow(['Name', 'Category', 'City', 'Country', 'Location', 'Overview', 'URL Link'])


    with open("scriptInput.txt", "rt") as input_lines:
        for index, line in enumerate(input_lines):
            country_name, city_name, city_link = parsing_script_input(line)
            dictionary = collect_category_link(city_link)
            activity_url_list = list(dictionary.values())   # within function, all collected activity links for the particular city
            category_list = list(dictionary.keys())
            # print(len(activity_url_list))

            # Multiprocessing for Collect_links

            # num_process for number of processes to be ran. Capped at 10 processes to prevent being blocked.
            if len(activity_url_list) < 11:
                num_process = len(activity_url_list)
            else:
                num_process = 10
            all_process = len(activity_url_list)  # Total number of processes that should run. Change this according to uni. Change this to 1 for testing.
            num_finish_process = 0  # Count for finished process
            count_process = 0  # Count number of processes running
            process_num = 0  # This is for the course type in collect_data function
            process = []
            values = []

            def get_link_process(process_num, count_process):  # Function to create and start process
                process_num = process_num + 1  # This is for the course type in collect_data function
                new_process = multiprocessing.Process(target=collect_links, args=(activity_url_list.pop(), category_list.pop(), country_name, city_name, process_num))
                process.append(new_process)
                new_process.start()
                count_process += 1

                return [process_num, count_process]

            def start_get_link_process():  # Function that will call the create process function.
                nonlocal process_num, count_process, all_process
                nonlocal values

                values = get_link_process(process_num, count_process)

                process_num = values[0]
                count_process = values[1]

            while True:
                if count_process < num_process and process_num < all_process:  # Check if there is still processes left to be run, create new process if needed
                    start_get_link_process()
                    print("Starting process")

                for proc in process:  # Loop that will check for status of process
                    proc.join(timeout=0)
                    if not proc.is_alive():
                        process.remove(proc)  # Remove the finished process from the list
                        print("Process Ended!")
                        num_finish_process += 1
                        print('Completed Processes:')
                        print(num_finish_process)
                        remain_proc = int(all_process) - int(num_finish_process)
                        print('Remaining Processes:')
                        print(remain_proc)
                        count_process -= 1
                        break

                if count_process == 0 and num_finish_process == all_process:
                    print("Collect Links process is done." + "\t\tTotal finished process " + str(num_finish_process))
                    break

    # Reading the Info from the UniquelinkList.csv file and placing the information into array lists for collect_data method.
    with open(uniqueLinkList_path, 'rt', encoding='utf-8', newline='') as activity_link:
        reader = csv.reader(activity_link)
        counter = 0                                 # Count how many links from the file.
        attraction_url_list = []                    # Stores all URL links from file.
        city_list = []                              # Stores all City names from file.
        country_list = []                           # Stores all country names from file.
        categ_list = []                             # Stores all category types from file.

        durl = 3                                    # The index of URL column from UniqueLinkList file
        dcity = 2                                   # The index of city name column from UniqueLinkList file
        dcountry = 1                                # The index of country name column from UniqueLinkList file
        dcategory = 0                               # The index of category type column from UniqueLinkList file

        for row in reader:
            attraction_url_list.append(row[durl])
            city_list.append(row[dcity])
            country_list.append(row[dcountry])
            categ_list.append(row[dcategory])
            counter += 1

        print('The total links are ' + str(counter))
        print('The total number of  process is ' + str(len(attraction_url_list)))

    # Multiprocessing for collect_data
    num_process = 10  # Number of processes running at one time. Change this to 1 for testing.
    all_process = len(attraction_url_list)  # Total number of processes that should run. Change this according to uni. Change this to 1 for testing.
    num_finish_process = 0  # Count for finished process
    count_process = 0  # Count number of processes running
    process_num = 0  # This is for the course type in collect_data function
    process = []
    values = []

    def get_data_process(process_num, count_process):  # Function to create and start process
        process_num = process_num + 1  # This is for the course type in collect_data function
        new_process = multiprocessing.Process(target=collect_data, args=(categ_list.pop(), country_list.pop(), city_list.pop(), attraction_url_list.pop(), process_num))
        process.append(new_process)
        new_process.start()
        count_process += 1

        return [process_num, count_process]

    def start_get_data_process():  # Function that will call the create process function.
        nonlocal process_num, count_process, all_process
        nonlocal values

        values = get_data_process(process_num, count_process)

        process_num = values[0]
        count_process = values[1]

    while True:
        if count_process < num_process and process_num < all_process:  # Check if there is still processes left to be run, create new process if needed
            start_get_data_process()
            print("Starting process")

        for proc in process:  # Loop that will check for status of process
            proc.join(timeout=0)
            if not proc.is_alive():
                process.remove(proc)  # Remove the finished process from the list
                print("Process Ended!")
                num_finish_process += 1
                print('Completed processes/links:')
                print(num_finish_process)
                remain_proc = int(all_process) - int(num_finish_process)
                print('Remaining processes/links:')
                print(remain_proc)
                count_process -= 1
                break

        if count_process == 0 and num_finish_process == all_process:
            print("Collect Data process is done." + "\t\tTotal finished process " + str(num_finish_process))
            break

    stop = timeit.default_timer()
    time_sec = stop - start
    time_min = int(time_sec / 60)
    time_hour = int(time_min / 60)

    time_run = str(format(time_hour, "02.0f")) + ':' + str(
        format((time_min - time_hour * 60), "02.0f") + ':' + str(format(time_sec - (time_min * 60), "^-05.1f")))
    print ("These are all the unscrapped sites" + str(unsupported_links))
    print("This code has completed running in: " + time_run)

if __name__ == '__main__':
    main()