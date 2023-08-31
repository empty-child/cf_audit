"""
Profile for xxxx

Date: xxxx-xx-xx
Author: xxxx
License: MIT
"""

# '''
# Where to get the latest feed.
# This URL points to the raw data of a GeoJSON file.
# Example: download_url = 'https://example.ch/data/myShop.geojson'
# '''
download_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/police_zurich_ch.geojson' #TODO

# '''
# What will be put into "source" tags.
# This indicates where the data is coming from. It could be a name or a website of a project collecting the data.
# Example: source = 'alltheplaces.xyz'
# '''
source = 'alltheplaces.xyz' #TODO

# '''
# Tags for querying with overpass api.
# For single tags. This selects objects with shop=electronics
#       query = '[shop=electronics]'
# For multiple of the same tag. This selects objects with shop=electronics OR shop=hifi
#       query = '[shop~"electronics|hifi"]'
# For multiple tags. This selects objects with shop=farm AND name=Hofladen*
#       query = '[shop=farm][name~"Hofladen*"]'
# '''
query = '[amenity=police]' #TODO

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm.
# Example: master_tags = ('name', 'website', 'addr:postcode', 'addr:city')
# '''
master_tags = () #TODO

# '''
# How close OSM point should be to register a match, in meters. Default is 100
# for electronics this can be very close together, but something like 10 meters leads to multiple new points,
# that should actually be duplicates.
# this issue should be looked into further for non-example datasets, and might need some adaptations for each dataset
# '''
max_distance = 100 #TODO

# '''
# Dataset points that are closer than this distance (in meters) will be considered duplicates of each other.
# '''
duplicate_distance = 0 #TODO

# Use bbox from dataset points (default). False = query whole world, [minlat, minlon, maxlat, maxlon] to override
# restrict bounding box, makes query much, much faster!
bbox = [47.1463, 8.3633, 47.5566, 8.9964]

# increase overpass timeout for large datasets!
overpass_timeout = 10000

# If set to True, unmatched OSM points will be deleted. Default is False: they are retagged instead.
delete_unmatched = False

# A fairly unique id of the dataset to query OSM, used for "ref:mos_parking" tags
# If you omit it, set explicitly "no_dataset_id = True"
no_dataset_id = True


# '''
# A function that gets OSM object tags and dataset point tags, and returns False if these points should not be matched.
# '''

def matches(osm_tags, external_tags):
    # TODO
    # This function is not always needed. If it does not increase the matching quality, remove it for better performance
    #
    # "name" and "brand:wikidata" might not be the best matching criteria. Replace them if needed.

    osm_name = osm_tags.get("name", '').lower()
    e_name = external_tags['name'].lower()
    if e_name in osm_name:
        return True
    '''
    osm_brand_wikidata = osm_tags.get("brand:wikidata", '')
    e_brand_wikidata = external_tags['brand:wikidata']
    if osm_brand_wikidata == e_brand_wikidata:
        return True
    '''
    return False


# '''
# A function to calculate weight of an OSM object. The only parameter is the object with e.g. tags and osm_type
# fields. It should return a number, which alters a calculated distance between this and dataset points.
# Positive numbers greater than 3 decrease distance (so priority=50 for a point 90 meters away from a dataset
# point makes it closer than an OSM point 45 meters away), negative numbers increase distance. Numbers between
# -3 and 3 are multiplied by max_distance.
# '''
# TODO
# This function is not always needed. It can provide better results than the matches() function with the downside of
# hard coded data values.
'''
def weight(osm_point):
    match_weight = 0

    # Possible content of osm_point:
    # OSMPoint(way 275037029 v4, 47.5449622, 9.2986158, action=None, tags={'addr:city': 'Amriswil',
    #   'addr:country': 'CH', 'addr:housenumber': '1', 'addr:postcode': '8580', 'addr:street': 'Weinfelderstrasse',
    #   'building': 'yes', 'name': 'Fust', 'shop': 'electronics', 'source': 'Bing', 'wheelchair': 'no'})
    
    name = osm_point.tags.get("name")
    if name is not None:
        if 'Fust' in name:
            match_weight = match_weight + 1
        else:
            match_weight = match_weight - 1

    brand_wikidata = osm_point.tags.get("brand:wikidata")
    if brand_wikidata is not None:
        if 'Q1227164' == brand_wikidata:
            match_weight = match_weight + 1
        else:
            match_weight = match_weight - 1
    
    return match_weight
'''


# '''
# A list of SourcePoint objects. Initialize with (id, lat, lon, {tags}).
# The fileobj attribute must be expected, even though it is not used here
# '''
def dataset(fileobj):
    # by the way the import happens, all imports and functions must be defined inside this function!
    import requests

    data_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/police_zurich_ch.geojson' #TODO # this is the same value as in "download_url"
    r = requests.get(data_url)
    result = r.json()
    json_data = result['features']

    data = []
    processed_ids = []
    for element in json_data:
        el_prop = element['properties']
        shop_id = el_prop['ref']

        # Not all entries have geometry set
        if 'geometry' in element:
            lat = element['geometry']['coordinates'][1]
            lon = element['geometry']['coordinates'][0]
        else:
            print(f'-- NO GEOMETRY for {shop_id}')

        tags = el_prop
        '''
        # TODO
        # This function is not always needed and can be omitted if the source data quality is high enough.
        # Simple split for street_address.
        # Bad splits to be expected! For example: "Some Street 12 A" --> "Some Street 12" + "A"
        if 'addr:housenumber' not in tags and 'addr:street_address' in tags:
            street_address = tags['addr:street_address'].split(" ")
            if len(street_address) > 1:
                tags['addr:housenumber'] = street_address.pop(len(street_address) - 1)
                tags['addr:street'] = ' '.join(street_address)
            else:
                tags['addr:street'] = street_address
            tags.pop('addr:street_address')  # remove now duplicate data

        # TODO
        # Not every tag is useful. By removing them we prevent the Conflator from adding it to OSM.
        tags.pop('branch')  # duplicate with addr:city
        '''
        # Remove undesired tag which is required by alltheplaces
        tags.pop('@spider')  # irrelevant for OSM

        if shop_id in processed_ids:
            print(f'-- Shop {shop_id} already present')
        else:
            processed_ids.append(shop_id)

            # Class SourcePoint() will be available after this file was imported during execution
            data.append(SourcePoint(shop_id, lat, lon, tags))

    return data
