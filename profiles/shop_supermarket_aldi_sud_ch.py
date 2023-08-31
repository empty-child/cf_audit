"""
Profile for Aldi Sud

Date: 2022-12-06
Author: OST
License: MIT
"""

# '''
# Where to get the latest feed
# '''
download_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/aldi_sud_ch.geojson'

# '''
# What will be put into "source" tags.
# '''
source = 'https://alltheplaces.xyz'

# '''
# Tags for querying with overpass api
# '''
query = '[shop=supermarket]'

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm
# '''
master_tags = ('name', 'opening_hours', 'website', 'phone', 'addr:postcode', 'addr:city', 'contact:phone', 'brand', 'brand:wikidata')

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
bbox = [45.7309, 5.8509, 47.8443, 10.5805]

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
# A function that gets OSM object tags and dataset point tags, and returns False if these points should not be matched.
# '''
def matches(osm_tags, external_tags):
    osm_name = osm_tags.get("name", '').lower()
    e_name = external_tags['name'].lower()
    if e_name in osm_name:
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
    import requests

    data_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/aldi_sud_ch.geojson'
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

        # Overwrite tags for which name missmatch
        tags['ref'] = tags['name']
        # Update brand name to match OSM naming convention
        tags['name'] = tags['brand'].lower().capitalize()
        tags.pop('brand')
        # Remove duplicate data
        tags.pop('addr:full')

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

        # Remove undesired tags
        tags.pop('@spider')  # irrelevant for OSM

        if shop_id in processed_ids:
            print(f'--- Shop {shop_id} already present')
        else:
            processed_ids.append(shop_id)

            # Class SourcePoint() will be available after this file was imported during execution
            data.append(SourcePoint(shop_id, lat, lon, tags))

    return data
