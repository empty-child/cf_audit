"""
Profile for Jumbo

Date: 2022-12-11
Author: OST
License: MIT
"""

# '''
# Where to get the latest feed.
# This URL points to the raw data of a GeoJSON file.
# Example: download_url = 'https://example.ch/data/myShop.geojson'
# '''
download_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/jumbo_ch.geojson'

# '''
# What will be put into "source" tags.
# This indicates where the data is coming from. It could be a name or a website of a project collecting the data.
# Example: source = 'alltheplaces.xyz'
# '''
source = 'alltheplaces.xyz'

# '''
# Tags for querying with overpass api.
# For single tags. This selects objects with shop=electronics
#       query = '[shop=electronics]'
# For multiple of the same tag. This selects objects with shop=electronics OR shop=hifi
#       query = '[shop~"electronics|hifi"]'
# For multiple tags. This selects objects with shop=farm AND name=Hofladen*
#       query = '[shop=farm][name~"Hofladen*"]'
# '''
query = '[shop~"doityourself|hardware"]'

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm.
# Example: master_tags = ('name', 'website', 'addr:postcode', 'addr:city')
# '''
master_tags = ('name', 'website')

# '''
# How close OSM point should be to register a match, in meters. Default is 100
# for electronics this can be very close together, but something like 10 meters leads to multiple new points,
# that should actually be duplicates.
# this issue should be looked into further for non-example datasets, and might need some adaptations for each dataset
# '''
max_distance = 400

# '''
# Dataset points that are closer than this distance (in meters) will be considered duplicates of each other.
# '''
duplicate_distance = 20

# Use bbox from dataset points (default). False = query whole world, [minlat, minlon, maxlat, maxlon] to override
# restrict bounding box, makes query much, much faster!
bbox = [45.7309, 5.8509, 47.8443, 10.5805]

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
    # Due to the fusion of "Coop Bau+Hobby" with "Jumbo" and the localisation based writing, this extra step is needed
    import re
    possible_names = ["coop", "jumbo", "hobby", "brico"]
    osm_name = osm_tags.get("name", '').lower()
    if re.search('|'.join(possible_names), osm_name):
        return True

    osm_brand_wikidata = osm_tags.get("brand:wikidata", '')
    e_brand_wikidata = external_tags['brand:wikidata']
    if osm_brand_wikidata == e_brand_wikidata:
        return True

    return False


# '''
# A list of SourcePoint objects. Initialize with (id, lat, lon, {tags}).
# The fileobj attribute must be expected, even though it is not used here
# '''
def dataset(fileobj):
    # by the way the import happens, all imports and functions must be defined inside this function!
    import requests

    data_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/jumbo_ch.geojson'
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

        # Remove undesired tag which is required by alltheplaces
        tags.pop('@spider')  # irrelevant for OSM

        if shop_id in processed_ids:
            print(f'-- Shop {shop_id} already present')
        else:
            processed_ids.append(shop_id)

            # Class SourcePoint() will be available after this file was imported during execution
            data.append(SourcePoint(shop_id, lat, lon, tags))

    return data
