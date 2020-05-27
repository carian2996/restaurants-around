import json
import string
import pandas as pd

from h3 import h3
from helpers import *

# TODO: Where should I place this?
street_slang = [
    'interior', 'city', 'mexico', 'df'
    , 'cdmx', 'calle', 'colonia', 'col'
    , 'cerrada', 'cda', 'av', 'ciudad', 'esquina'
    , 'cp', 'loc', 'secc', 'local', 'seccion'
    , 'num', 'ext', 'numero', 'exterior'
    , 'avenida', 'delegacion', 'no'
]

if __name__ == "__main__":
    
    rappi = pd.read_csv('../scraper/data/rappi_revolucion258_noon.csv')
    eats = pd.read_csv('../scraper/data/ue_revolucion258_noon.csv')

    RES = 12

    df_eats_hexes = build_hexes(eats, RES)
    df_rappi_hexes = build_hexes(rappi, RES)

    # More duplicates? This is due to restaurants sharing the same location.
    # We'll handle that later. First we need to identify NO OVERLAPING restos.
    df_hexes = df_eats_hexes.merge(df_rappi_hexes, on='hex_id', how='outer')
    df_hexes = (
        df_hexes
        [['hex_id', 'id_x', 'id_y']]
        .rename(columns={
            'id_x': 'eats'
            , 'id_y': 'rappi'
        })
    )
    
    df_agg_hexes = (
        df_hexes
        .groupby('hex_id')
        .count()
        .reset_index(drop=False)
    )

    df_agg_hexes['hex_platform'] = df_agg_hexes.apply(lambda row: which_platform(row['eats'], row['rappi']), axis=1)
    df_agg_hexes['total_restos'] = df_agg_hexes.apply(lambda row: row['eats'] + row['rappi'], axis=1)

    df_hexes = (
        df_hexes
        .melt(id_vars=['hex_id'], value_vars=['eats', 'rappi'])
        .rename(columns={'variable': 'platform', 'value': 'id'})
        .drop_duplicates()
        .dropna()
    )

    df_hexes = get_neighbors(df_hexes, 2)
    df_hexes = df_hexes.merge(df_agg_hexes[['hex_id', 'hex_platform']])

    df_all_hexes = (
        df_hexes
        .merge(
            pd.concat([df_eats_hexes, df_rappi_hexes])
            # TODO: Can you get rid of this part? 
            # if build_hexes creates geoms it'll blow up
            [['hex_id', 'id', 'platform']]
        )
    )

    all_restos = pd.concat([eats, rappi])
    no_neighbors = df_all_hexes.neighbors.isna()

    df_no_neighbors = df_all_hexes[no_neighbors].reset_index(drop=True)
    df_no_neighbors = (
        df_no_neighbors
        [['id', 'platform', 'hex_id', 'hex_platform']]
        .merge(all_restos[['id', 'platform', 'name', 'address']], on=['id', 'platform'])
        )

    df_no_neighbors_dups = find_dups(
        df_no_neighbors
        , street_slang
        , ngram=2
        , threshold=0.45
        , includes_hex=True
        )   

    df_unique_no_neighbors = df_no_neighbors.merge(
        get_uniques(df_no_neighbors_dups)
        , left_on='id'
        , right_on='dup_id'
        , how='left'
        ) 

    df_unique_no_neighbors['uuid'] = df_unique_no_neighbors.apply(lambda row: row['id']+'::'+row['platform'] if str(row['uuid'])=='nan' else row['uuid'], axis=1)
    df_restos_no_neighbors = df_unique_no_neighbors[['uuid', 'name']].merge(all_restos[['name', 'lat', 'lng']])
    df_restos_no_neighbors = give_format(df_restos_no_neighbors)
    
    # TODO: Can we fit this into one main function?
    # Worked with only two restaurants, but what if we have a dozen?
    df_with_neighbors = df_all_hexes[~no_neighbors].reset_index(drop=True)
    df_with_neighbors = (
        df_with_neighbors
        [['id', 'platform', 'hex_id', 'hex_platform']]
        .merge(all_restos[['id', 'platform', 'name', 'address']], on=['id', 'platform'])
        )

    df_with_neighbors_dups = find_dups(
        df_with_neighbors
        , street_slang
        , ngram=2
        , threshold=0.5
        )   

    df_unique_with_neighbors = df_with_neighbors.merge(
        get_uniques(df_with_neighbors_dups)
        , left_on='id'
        , right_on='dup_id'
        , how='left'
        ) 

    df_unique_with_neighbors['uuid'] = df_unique_with_neighbors.apply(lambda row: row['id']+'::'+row['platform'] if str(row['uuid'])=='nan' else row['uuid'], axis=1)
    df_restos_with_neighbors = df_unique_with_neighbors[['uuid', 'name']].merge(all_restos[['name', 'lat', 'lng']])
    df_restos_with_neighbors = give_format(df_restos_with_neighbors)

    df_restos = pd.concat([df_restos_no_neighbors, df_restos_with_neighbors])
    df_restos = df_restos.sort_values('id').reset_index(drop=True)
    df_restos.to_csv('unique_restos.csv', header=True, index=False)
    print('Done!')