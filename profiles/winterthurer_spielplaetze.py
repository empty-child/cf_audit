"""
Profile for Winterthurer Spielplaete

Date: 2023-08-30
Author: OST
License: MIT
"""

# '''
# Where to get the latest feed
# '''
download_url = 'https://gitlab.ost.ch/ifs/geometalab/cf_audit/-/raw/master/profiles/geojson/winterthurer_spielplaetze.geojson'

# '''
# What will be put into "source" tags.
# '''
source = 'https://alltheplaces.xyz'

# '''
# Tags for querying with overpass api
# '''
query = '[leisure~"playground|park"]'

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm
# '''
master_tags = ('name', 'access')

# '''
# How close OSM point should be to register a match, in meters. Default is 100
# for electronics this can be very close together, but something like 10 meters leads to multiple new points,
# that should actually be duplicates.
# this issue should be looked into further for non-example datasets, and might need some adaptations for each dataset
# '''
max_distance = 500

# '''
# Dataset points that are closer than this distance (in meters) will be considered duplicates of each other.
# '''
duplicate_distance = 20

# '''
# Use bbox from dataset points (default). False = query whole world, [minlat, minlon, maxlat, maxlon] to override
# restrict bounding box, makes query much, much faster!
# '''
bbox = [8.655,47.449,8.811,47.549]

# '''
# increase overpass timeout for large datasets!
# '''
overpass_timeout = 10000

# '''
# If set to True, unmatched OSM points will be deleted. Default is False: they are retagged instead.
# '''
delete_unmatched = False

# '''
# A fairly unique id of the dataset to query OSM, used for "ref:mos_parking" tags
# If you omit it, set explicitly "no_dataset_id = True"
# '''
no_dataset_id = True


# '''
# A list of SourcePoint objects. Initialize with (id, lat, lon, {tags}).
# The fileobj attribute must be expected, even though it is not used here
# '''
def dataset(fileobj):
    # by the way the import happens, all imports and functions must be defined inside this function!
    import requests
    

    data_url = 'https://gitlab.ost.ch/ifs/geometalab/cf_audit/-/raw/master/profiles/geojson/winterthurer_spielplaetze.geojson'
    r = requests.get(data_url)
    
    result = r.json()
    json_data = result['features']

    data = []
    processed_ids = []
    
    for element in json_data:
        el_prop = element['properties']
        shop_id = element['id']

        # Not all entries have geometry set
        if 'geometry' in element:
            lat = element['geometry']['coordinates'][1]
            lon = element['geometry']['coordinates'][0]
        else:
            print(f'-- NO GEOMETRY for {shop_id}')

        tags = el_prop

        # Remove undesired tag which is required by alltheplaces
        tags.pop('@spider')  # irrelevant for OSM

        if shop_id in processed_ids:
            print(f'-- Shop {shop_id} already present')
        else:
            processed_ids.append(shop_id)

            # Class SourcePoint() will be available after this file was imported during execution            
            data.append(SourcePoint(shop_id, lat, lon, tags))

    return data
