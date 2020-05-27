import re
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix
from nltk.corpus import stopwords
import sparse_dot_topn.sparse_dot_topn as ct
from sklearn.feature_extraction.text import TfidfVectorizer

from h3.h3 import geo_to_h3, h3_to_geo_boundary, k_ring_distances

def build_hexes(df, hex_res, create_geom=False):
    cols = ['id', 'platform', 'lat', 'lng']
    if not set(cols).issubset(df.columns): 
        print('Columns required: ', ', '.join(cols))
        return(df)
    
    df = df[cols].reset_index(drop=True).copy()
    df['hex_id'] = df.apply(lambda row: geo_to_h3(row['lat'], row['lng'], res=hex_res), axis=1)
    
    if create_geom:
        polygons = []
        for h in df.hex_id:
            polygons.append({
                "type" : "Polygon"
                , "coordinates": [h3_to_geo_boundary(h3_address=h, geo_json=True)]
            })
        df['geometry'] = pd.Series(polygons)
    
    return(df)

# TODO: Change to not depend on Eats and Rappi services
def which_platform(eats, rappi):
    if (0 < eats) and (0 < rappi):
        return 'both'
    elif (eats == 0) and (0 < rappi):
        return 'rappi'
    elif (0 < eats) and (rappi == 0):
        return 'eats'

def get_neighbors(df, rings=1):
    for i, row in df.iterrows():

        lst_rings = []
        for r in range(1, rings+1):
            lst_rings += list(k_ring_distances(row['hex_id'], rings)[r])
        
        neighbors = df[df.hex_id.isin(lst_rings)].id.tolist()
        
        if 0 < len(neighbors):
            df.loc[i, 'neighbors'] = ', '.join([x for x in neighbors if str(x) != 'nan'])
            
    return(df)

def find_dups(df, slang, threshold=0.5, ngram=2, hex_res=12, includes_hex_platform=True, includes_hex=False):
    df_aux = df.reset_index(drop=True).copy()
    
    df_aux['name'] = df_aux.name.str.lower()
    df_aux['name'] = df_aux.name.str.replace('[^\w\s]','')
    df_aux['name'] = df_aux.name.str.replace('\d+', '')
    df_aux['name'] = df_aux.name.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    df_aux['name'] = df_aux.name.str.replace('\d+', '')
    df_aux['name'] = df_aux.name.apply(lambda x: ' '.join([item for item in x.split() if item not in stopwords.words('spanish')]))
    df_aux['name'] = df_aux.name.apply(lambda x: ' '.join( [w for w in x.split() if len(w)>1]))
    
    df_aux['address'] = df_aux.address.str.lower()
    df_aux['address'] = df_aux.address.str.replace('[^\w\s]','')
    df_aux['address'] = df_aux.address.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    df_aux['address'] = df_aux.address.apply(lambda x: ' '.join([item for item in str(x).split() if item not in slang]))
    df_aux['address'] = df_aux.address.apply(lambda x: ' '.join([item for item in x.split() if item not in stopwords.words('spanish')]))
    df_aux['address'] = df_aux.address.str.replace('nan', '')

    df_aux['street'] = df_aux.address.apply(lambda x: re.match('^(.*?[0-9]+)', x).group(1) if re.match('^(.*?[0-9]+)', x) is not None else '')
    df_aux['short_hex_id'] = df_aux.hex_id.apply(lambda x: x[int(hex_res/2):])
    
    df_aux['full_address'] = df_aux['id']
    if includes_hex_platform: df_aux['full_address'] += (' ' +  df_aux['hex_platform'])
    if includes_hex: df_aux['full_address'] += (' ' + df_aux['short_hex_id'])
    df_aux['full_address'] += ' ' + df_aux['name']
    df_aux['full_address'] = df_aux.apply(lambda row: row['full_address'] + ' ' + row['street'] if row['street'] != '' else '', axis=1)
    
    df_dups = df_aux.reset_index(drop=True).copy()

    full_address = df_dups['full_address']
    vectorizer = TfidfVectorizer(ngram_range=(1, ngram), sublinear_tf=True)
    tf_idf_matrix = vectorizer.fit_transform(full_address)
    
    matches = _awesome_cossim_top(tf_idf_matrix, tf_idf_matrix.transpose(), ntop=5)
    matches_df = _get_matches_df(matches, full_address)
    matches_df = matches_df[matches_df.similarity.between(threshold, 0.99)]
    matches_df = matches_df.sort_values('similarity', ascending=False)
    
    matches_df['left_side'] = matches_df.left_side.apply(lambda x: ', '.join(x.split()[:2]))
    matches_df['right_side'] = matches_df.right_side.apply(lambda x: ', '.join(x.split()[:2]))
    matches_df = matches_df.drop_duplicates(subset=['similarity']).reset_index(drop=True)
    
    df_left = matches_df.left_side.str.split(expand=True)
    df_left[0] = df_left[0].str.replace(',', '')
    df_left.columns = ['left_id', 'left_hex_platform']

    df_right = matches_df.right_side.str.split(expand=True)
    df_right[0] = df_right[0].str.replace(',', '')
    df_right.columns = ['right_id', 'right_hex_platform']
    
    df_out = pd.concat([df_left, df_right, matches_df[['similarity']]], axis=1)
    df_out[
        (df_out['left_hex_platform'] == 'both') | 
        (df_out['left_hex_platform'] != df_out['right_hex_platform'])
    ]
    
    return(df_out)

def get_uniques(df):

    df['uuid'] = (
        df.apply(lambda row: 
        _find_longest(
            row['left_id'].replace('-', ' ')
            , row['right_id'].replace('-', ' ')
            ), axis=1)
        )
    df = df[3 <= df.uuid.str.len()]
    df = df[~df.uuid.isna()].reset_index(drop=True)
    df['uuid'] = df.uuid.apply(lambda x: '-'.join( [w for w in x.split() if 3 <= len(w)]))
    df['uuid'] = df['uuid'] + '::both'

    df = (
        df
        .melt(id_vars=['uuid'], value_vars=['left_id', 'right_id'])
        .drop('variable', axis=1)
        .rename(columns={'value': 'dup_id'})
        .sort_values('uuid')
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return(df)

def _awesome_cossim_top(A, B, ntop, lower_bound=0):
  
    A = A.tocsr()
    B = B.tocsr()
    M, _ = A.shape
    _, N = B.shape
 
    idx_dtype = np.int32
 
    nnz_max = M*ntop
 
    indptr = np.zeros(M+1, dtype=idx_dtype)
    indices = np.zeros(nnz_max, dtype=idx_dtype)
    data = np.zeros(nnz_max, dtype=A.dtype)

    ct.sparse_dot_topn(
        M, N, np.asarray(A.indptr, dtype=idx_dtype),
        np.asarray(A.indices, dtype=idx_dtype),
        A.data,
        np.asarray(B.indptr, dtype=idx_dtype),
        np.asarray(B.indices, dtype=idx_dtype),
        B.data,
        ntop,
        lower_bound,
        indptr, indices, data)

    return csr_matrix((data,indices,indptr),shape=(M,N))

def _get_matches_df(sparse_matrix, name_vector, top=1000):
    non_zeros = sparse_matrix.nonzero()
    
    sparserows = non_zeros[0]
    sparsecols = non_zeros[1]
    
    if top:
        nr_matches = top
    else:
        nr_matches = sparsecols.size
    
    left_side = np.empty([nr_matches], dtype=object)
    right_side = np.empty([nr_matches], dtype=object)
    similarity = np.zeros(nr_matches)
    
    for index in range(0, nr_matches):
        left_side[index] = name_vector[sparserows[index]]
        right_side[index] = name_vector[sparsecols[index]]
        similarity[index] = sparse_matrix.data[index]
    
    return pd.DataFrame({'left_side': left_side,
                          'right_side': right_side,
                           'similarity': similarity})

def _hash_sequence(string, k):

    dictionary={}
    for i in range(len(string)-(k-1)):
        sequence = string[i:i+k]
        dictionary.setdefault(sequence,[]).append(i)
    return dictionary

def _intersects(string1, string2, k): #what if k=0?
    dictionary = _hash_sequence(string1, k)

    for i in range(len(string2)-1): #O(n) for sybstring in string

        if string2[i:i+k] in dictionary: #O(n
            return string2[i:i+k]
    return None

def _find_longest(string1, string2):
    longest_seq = None

    for i in range(1, min(len(string1), len(string2))+1):
        # Store the current iteration's intersection
        current_seq = _intersects(string1, string2, i)

        # If this was one character too long, return.
        # Else, a longer intersection was found. Store it.
        if current_seq == None:
            return longest_seq
        else:
            longest_seq = current_seq

    # If we get here, the strings were the same.
    # For consistency, return longest_seq and its length.
    return longest_seq

def give_format(df):
    df = df.drop_duplicates(subset=['uuid'])
    df = pd.concat([df.uuid.str.split('::', expand=True), df[['name', 'lat', 'lng']]], axis=1)
    df.columns = ['id', 'platform', 'name', 'lat', 'lng']
    # df = df.sort_values('id')
    df.reset_index(drop=True, inplace=True)
    
    return(df)