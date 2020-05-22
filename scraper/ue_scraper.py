# I/O modules
import json
import configparser

# Scraping tools
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

if __name__ == '__main__':

    with webdriver.Chrome('chromedriver', options=chrome_options) as driver:

        print(str(datetime.now()), '- Initiate scraping...')
        
        # Reading address from text file
        config = configparser.ConfigParser()
        config.read(sys.argv[1])
        ADDRESS = config['location']['address']
        print(str(datetime.now()), '- Looking for resturants in:')
        print('\n', ADDRESS, '\n')

        # TODO: /mx is particular for Mexico, I need to adapt this part
        # based on input address rather than a fixed value

        # Iniate driver in URL
        URL = config['location']['url']
        driver.get(URL)
        
        time.sleep(3) # from time to tim I'll wait a cuple of seconds
        print(str(datetime.now()), '- Input address...')
        # Looking for input combobox in main page
        location_input = driver.find_element_by_id('location-typeahead-home-input')
        location_input.send_keys(ADDRESS)

        time.sleep(3)
        print(str(datetime.now()), '- Searching restaurants...')
        # Sending keys to establish the ADDRESS
        search_button = driver.find_element_by_xpath('//button[text()="Buscar comida"]')
        search_button.click()

        time.sleep(3)
        # Once our ADDRESS was inputed, we need all restaurants around there

        # TODO: Apparently /near-me is generic and independent from the city or address
        # I'm good with this, but vulnerable...
        driver.get(URL+'/near-me')

        time.sleep(3)
        print(str(datetime.now()), '- Retriving food categories...')
        # Uber Eats groups restaurants near you in food categories
        categories = driver.find_elements_by_xpath('//a[@href]')
        
        # FIXED: Because web elements are uniques per interaction, 
        # coming back to previous page will change the elements saved
        # in categories and getting its attributes will throw an error

        # I'll save only the href and each iteration will use
        # the driver to find the element and click it
        
        # Lots of useless links are stored, only interested in food categories and restaurant information
        categories_hrefs = [c.get_attribute("href") for c in categories if re.search(r'.*\/near-me\/.*([a-z])$', c.get_attribute("href"))]
        
        data = {}
        for h in categories_hrefs:
            cate = h.replace(URL + '/near-me/', '')

            data[cate] = {}
            
            time.sleep(5)
            data[cate]['web_href'] = h.replace('https://www.ubereats.com', '')

            time.sleep(3)
            # FIXED: Some elements can be unavailable at moments, adding an try-expection
            try:
                # I iterate for all categories available and go to another page
                driver.find_element_by_xpath("//a[@href='" + data[cate]['web_href'] + "']").click()
                
            except Exception as e:
                print('Element', data[cate]['web_href'], 'is not clickable at point')
                continue

            data[cate]['restaurants'] = {}
            
            time.sleep(3)
            print('\n' + str(datetime.now()), '- Looking restaurants for:', cate, '\n')
            # Same process... lots of links, I only need links ot get restaurant's data
            restaurants = driver.find_elements_by_xpath("//a[@href]")
            restaurants_hrefs = [c.get_attribute("href") for c in restaurants if re.search(r'\/food-delivery\/', c.get_attribute("href"))]
            
            for r in restaurants_hrefs:
                # TODO: Only works for Mexico City
                id = r.replace(URL + '/mexico-city/food-delivery/', '').split('/')[0]
                try:
                    name = driver.find_element_by_xpath("//a[@href='" + r.replace(URL[:-3], '') + "']").text
                    data[cate]['restaurants'][id] = {}
                    data[cate]['restaurants'][id]['name'] = name
                    print(name)
                except Exception as e:
                    continue
            
            driver.back()

        print('\n')
        with open('data.json', 'w', encoding='utf8') as f: 
            json.dump(data, f, ensure_ascii=False)

        print(str(datetime.now()), '- Done!')