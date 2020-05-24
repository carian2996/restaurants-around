# I/O modules
from parser.parser import parse
import configparser
import json

# Utilities
import sys
import time
import requests
from datetime import datetime

CHECK_COVERAGE = 'https://services.mxgrability.rappi.com/api/base-crack/has-coverage?lat={}&lng={}'
CHECK_CATALOG = 'https://services.mxgrability.rappi.com/api/restaurant-bus/stores/catalog/home'

if __name__ == '__main__':
    
    print(str(datetime.now()), '- Initiate scraping...')
    # Reading address from text file
    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    ADDRESS = config['location']['address']
    LAT = config['location']['latitude']
    LNG = config['location']['longitude']
    OUTPUT = config['location']['output']

    print(str(datetime.now()), '- Looking for restaurants in:')
    print('\n', ADDRESS, '\n')

    get_coverage = requests.get(CHECK_COVERAGE.format(LAT, LNG))

    if json.loads(get_coverage.text)['has_coverage']:
        d = {"lat": LAT, "lng": LNG, "store_type": "restaurant", "is_prime": "false"}
        print(str(datetime.now()), '- Initiate POST request...')
        post_catalog = requests.post(CHECK_CATALOG, json=d)

        print(str(datetime.now()), '- Loading response as JSON')
        catalog = json.loads(post_catalog.text)
        N_RESTOS = len(catalog['stores'])

        print(str(datetime.now()), '- Restaurants retrived:', N_RESTOS)

        CUISINES = {}
        for tag in catalog['tags']: CUISINES[tag['id']] = tag['name']

        data = {}
        print(str(datetime.now()), '- Getting information from restaurants', '\n')
        for n in range(N_RESTOS):
            
            details = catalog['stores'][n]
            resto_id = details['friendly_url']['friendly_url']
            data[resto_id] = {}

            if 'name' in details.keys(): 
                data[resto_id]['name'] = details['name']
                print(str(n)+'.', data[resto_id]['name'])
            
            if 'tags' in details.keys(): 
                servesCuisine = []
                for tag in details['tags']:
                    try:
                        cuisine = CUISINES[tag]
                    except Exception as e:
                        pass
                    servesCuisine.append(cuisine)
                data[resto_id]['servesCuisine'] = servesCuisine
            
            if 'location' in details.keys(): data[resto_id]['geo'] = details['location']
            if 'price_range' in details.keys(): data[resto_id]['priceRange'] = details['price_range']
            if 'address' in details.keys(): data[resto_id]['address'] = details['address']
            if 'telephone' in details.keys(): data[resto_id]['telephone'] = ''
            
            if 'aggregateRating' in details.keys(): 
                d = {
                    "ratingValue": details['rating']['score']
                    , "reviewCount": details['rating']['total_reviews']
                    }
                data[resto_id]['aggregateRating'] = d
            
            if 'schedules' in details.keys(): data[resto_id]['openingHoursSpecification'] = details['schedules']
    
        print('\n')
        with open('./data/rappi_'+OUTPUT, 'w', encoding='utf8') as f: 
            json.dump(data, f, ensure_ascii=False)

        df = parse(data, 'rappi')
        if df is not None:
            df.to_csv(('./data/rappi_'+OUTPUT).replace('json', 'csv'), index=False)
        
        print(str(datetime.now()), '- Done!')
    
    else:
        print('No coverage for this address')

