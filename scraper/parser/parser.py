import json
import pandas as pd

def parse(json, platform):
    
    if platform in ['eats', 'rappi']:
        data = json
        df = pd.DataFrame(list(data.keys()), columns=['id'])

        ids, resto_name, lat, lng, cuisine = [[] for _ in range(5)]

        for r in df.id:
            if len(data[r]) == 0: continue
            ids.append(r)
            resto_name.append(data[r]['name'])
            lat.append(data[r]['geo'][0])
            lng.append(data[r]['geo'][1])
            cuisine.append(', '.join(data[r]['servesCuisine']))

        features = pd.DataFrame({'id': ids, 'name': resto_name, 'lat': lat, 'lng': lng, 'cuisine': cuisine})
        df = df.merge(features)
        df['platform'] = platform

        return(df)
    else:
        print('Platform not available. Use "eats" or "rappi".')
        return(None)