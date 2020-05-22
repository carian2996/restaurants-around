# I/O modules
import csv
import json
import configparser

# Scraping tools
# from selenium.webdriver.support.ui import Select, WebDriverWait
# from selenium.webdriver.common.keys import Keys
from selenium import webdriver

# Utilities
import sys
import re
import time
from datetime import datetime

# Driver options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

URL = 'https://www.ubereats.com/mx'
# ADDRESS = 'Avenida Revolución 258, Tacubaya, Mexico City, CDMX'

if __name__ == '__main__':

    with webdriver.Chrome('chromedriver', options=chrome_options) as driver:

        print(str(datetime.now()), '- Initiate scraping...')
        
        config = configparser.ConfigParser()
        config.read(sys.argv[1])
        ADDRESS = config['location']['address']
        print(str(datetime.now()), '- Looking for resturants in:')
        print('\n', ADDRESS, '\n')

        driver.get(URL)
        
        time.sleep(3)
        print(str(datetime.now()), '- Input address...')
        location_input = driver.find_element_by_id('location-typeahead-home-input')
        location_input.send_keys(ADDRESS)

        time.sleep(3)
        print(str(datetime.now()), '- Searching restaurants...')
        search_button = driver.find_element_by_xpath('//button[text()="Buscar comida"]')
        search_button.click()

        time.sleep(3)
        driver.get(URL+'/near-me')

        time.sleep(3)
        print(str(datetime.now()), '- Retriving food categories...')
        categories = driver.find_elements_by_xpath('//a[@href]')
        
        # TODO: Because web elements are uniques per interaction, 
        # coming back to previous page will change the elements saved
        # in categories and getting its attributes will throw an error

        # FIXED: I'll save only the href and each iteration will use
        # the driver to find the element and click it
        
        categories_hrefs = [c.get_attribute("href") for c in categories if re.search(r'.*\/near-me\/.*([a-z])$', c.get_attribute("href"))]
        
        data = {}
        for h in categories_hrefs:
            cate = h.replace('https://www.ubereats.com/mx/near-me/', '')

            if cate != 'pizza': continue
            data[cate] = {}
            
            time.sleep(3)
            data[cate]['web_href'] = h.replace('https://www.ubereats.com', '')

            time.sleep(3)
            driver.find_element_by_xpath("//a[@href='" + data[cate]['web_href'] + "']").click()

            data[cate]['restaurants'] = {}
            
            time.sleep(3)
            print(str(datetime.now()), '- Looking restaurants related to:', cate, '\n')
            restaurants = driver.find_elements_by_xpath("//a[@href]")
            restaurants_hrefs = [c.get_attribute("href") for c in restaurants if re.search(r'\/food-delivery\/', c.get_attribute("href"))]
            
            for r in restaurants_hrefs:
                # print(r.text)
                try:
                    id = r.replace('/mx/mexico-city/food-delivery/', '').split('/')[0]
                    try:
                        name = driver.find_element_by_xpath("//a[@href='" + r.replace('https://www.ubereats.com', '') + "']").text
                        data[cate]['restaurants'][id] = {}
                        data[cate]['restaurants'][id]['name'] = name
                        print(name)
                    except Exception as e:
                        print('Error while getting name element')
                        continue

                except Exception as e:
                    print('Error while getting link from', r.text)
                    continue
            
            driver.back()

        print()
        with open('data.json', 'w') as jsn: json.dump(data, jsn)
        time.sleep(5)