# I/O modules
import json
import configparser

# Scraping tools
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

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
        
        time.sleep(5) # from time to time I'll wait a couple of seconds
        print(str(datetime.now()), '- Input address...')
        # Looking for input combobox in main page
        location_input = driver.find_element_by_id('location-typeahead-home-input')
        location_input.send_keys(ADDRESS)

        time.sleep(3)
        print(str(datetime.now()), '- Getting restaurants...\n')
        # Sending keys to establish the ADDRESS
        search_button = driver.find_element_by_xpath('//button[text()="Buscar comida"]')
        search_button.click()
        time.sleep(5)

        # TODO: Apparently /near-me path is not showing all restos. I'll change this 
        # to use restaurants displayed by the Feed end point. Feed doesn't show all
        # restaurants at once, so I need to click "See more" button until page display them all
        more_exist = True
        while more_exist:
            try:
                more_button = driver.find_element_by_xpath('//button[text()="Mostrar más"]')
                more_button.click()
                time.sleep(5)
            except NoSuchElementException:
                more_exist = False
            
        restaurants = driver.find_elements_by_xpath("//a[@href]")
        restaurants_hrefs = [c.get_attribute("href") for c in restaurants if re.search(r'\/food-delivery\/', c.get_attribute("href"))]
        restaurants_hrefs = list(dict.fromkeys(restaurants_hrefs))
        
        N_RESTOS = len(restaurants_hrefs)
        print(str(datetime.now()), '- Restaurants retrived:', N_RESTOS)
        
        data = {}
        for n, r in enumerate(restaurants_hrefs, start=1):
            try:
                # Visit restaurant page to get detailed data
                driver.get(r)
                time.sleep(5)
                
                # TODO: Only works for Mexico City. Removes random identifier at the end
                resto_id = r.replace(URL + '/mexico-city/food-delivery/', '').split('/')[0]
                data[resto_id] = {}
                
                try:
                    script = driver.find_element_by_xpath("//script[@type='application/ld+json']")
                    details = json.loads(script.get_attribute('innerHTML'))

                    print(n+'.', details['name'])
                    
                    if 'name' in details.keys(): data[resto_id]['name'] = details['name']
                    if 'servesCuisine' in details.keys(): data[resto_id]['servesCuisine'] = details['servesCuisine']
                    if 'geo' in details.keys(): data[resto_id]['geo'] = [details['geo']['latitude'], details['geo']['longitude']]
                    if 'priceRange' in details.keys(): data[resto_id]['priceRange'] = details['priceRange']
                    if 'address' in details.keys(): data[resto_id]['address'] = details['address']
                    if 'telephone' in details.keys(): data[resto_id]['telephone'] = details['telephone']
                    if 'aggregateRating' in details.keys(): data[resto_id]['aggregateRating'] = details['aggregateRating']
                    if 'openingHoursSpecification' in details.keys(): data[resto_id]['openingHoursSpecification'] = details['openingHoursSpecification']
                
                except Exception as e:
                    print('No details for:', resto_id)
                    continue
            
            except Exception as e:
                raise print(e)
        
        print('\n')
        with open('./data/ue_'+OUTPUT, 'w', encoding='utf8') as f: 
            json.dump(data, f, ensure_ascii=False)

        driver.quit()
        print(str(datetime.now()), '- Done!')
