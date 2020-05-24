# I/O modules
from parser.parser import parse
import configparser
import json
import csv

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
        URL = config['location']['url']
        OUTPUT = config['location']['output']
        
        print(str(datetime.now()), '- Looking for restaurants in:')
        print('\n', ADDRESS, '\n')

        # TODO: /mx is particular for Mexico, I need to adapt this part
        # based on input address rather than a fixed value

        # Initiate driver in URL
        driver.get(URL)
        
        time.sleep(5) # from time to tim I'll wait a couple of second3s
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
        # Once our ADDRESS was inputted, we need all restaurants around there

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
        for c in categories_hrefs:
            cate = c.replace(URL + '/near-me/', '')
            time.sleep(5)

            data[cate] = {}
            
            time.sleep(3)
            data[cate]['web_href'] = c.replace('https://www.ubereats.com', '')

            time.sleep(3)
            # FIXED: Some elements can be unavailable at moments, adding an try-expection
            try:
                # I iterate for all categories available and go to another page
                driver.get(c)
                
            except Exception as e:
                raise print(e)

            data[cate]['restaurants'] = {}
            
            time.sleep(3)
            print('\n' + str(datetime.now()), '- Looking restaurants for:', cate, '\n')
            # Same process... lots of links, I only need links ot get restaurant's data
            restaurants = driver.find_elements_by_xpath("//a[@href]")
            restaurants_hrefs = [c.get_attribute("href") for c in restaurants if re.search(r'\/food-delivery\/', c.get_attribute("href"))]
            
            for r in restaurants_hrefs:
                time.sleep(1)
                try:
                    # Visit restaurant page to get detailed data
                    driver.get(r)
                    
                    try:
                        script = driver.find_element_by_xpath("//script[@type='application/ld+json']")
                    except Exception as e:
                        continue
                    details = json.loads(script.get_attribute('innerHTML'))

                    # TODO: Only works for Mexico City. Removes random identifier at the end
                    resto_id = details['@id'].replace(URL + '/mexico-city/food-delivery/', '').split('/')[0] 
                    
                    data[cate]['restaurants'][resto_id] = {}
                    
                    print(details['name'])

                    if 'name' in details.keys(): data[cate]['restaurants'][resto_id]['name'] = details['name']
                    if 'servesCuisine' in details.keys(): data[cate]['restaurants'][resto_id]['servesCuisine'] = details['servesCuisine']
                    if 'geo' in details.keys(): data[cate]['restaurants'][resto_id]['geo'] = [details['geo']['latitude'], details['geo']['longitude']]
                    if 'priceRange' in details.keys(): data[cate]['restaurants'][resto_id]['priceRange'] = details['priceRange']
                    if 'address' in details.keys(): data[cate]['restaurants'][resto_id]['address'] = details['address']
                    if 'telephone' in details.keys(): data[cate]['restaurants'][resto_id]['telephone'] = details['telephone']
                    if 'aggregateRating' in details.keys(): data[cate]['restaurants'][resto_id]['aggregateRating'] = details['aggregateRating']
                    if 'openingHoursSpecification' in details.keys(): data[cate]['restaurants'][resto_id]['openingHoursSpecification'] = details['openingHoursSpecification']
                
                except Exception as e:
                    raise print(e)
        
        print('\n')
        with open('./data/ue_'+OUTPUT, 'w', encoding='utf8') as f: 
            json.dump(data, f, ensure_ascii=False)

        df = parse(data, 'eats')
        if df is not None:
            df.to_csv(('./data/ue_'+OUTPUT).resplace('json', 'csv'))

        driver.quit()
        print(str(datetime.now()), '- Done!')
