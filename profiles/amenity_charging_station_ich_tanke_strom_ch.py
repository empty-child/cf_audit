"""
Profile for CH charging station

Date: 2022-12-08
Author: OST
License: MIT
"""

# '''
# Where to get the latest feed
# '''
download_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/ich_tanke_strom.geojson'

# '''
# What will be put into "source" tags.
# '''
source = 'https://alltheplaces.xyz'

# '''
# Tags for querying with overpass api
# '''
query = '[amenity=charging_station]'

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm
# '''
master_tags = ('name', 'website', 'operator', 'access', 'operator:wikidata')

# '''
# How close OSM point should be to register a match, in meters. Default is 100
# for electronics this can be very close together, but something like 10 meters leads to multiple new points,
# that should actually be duplicates.
# this issue should be looked into further for non-example datasets, and might need some adaptations for each dataset
# '''
max_distance = 100

# '''
# Dataset points that are closer than this distance (in meters) will be considered duplicates of each other.
# '''
duplicate_distance = 1

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
# A list of SourcePoint objects. Initialize with (id, lat, lon, {tags}).
# The fileobj attribute must be expected, even though it is not used here
# '''
def dataset(fileobj):
    # by the way the import happens, all imports and functions must be defined inside this function!
    import requests

    data_url = 'https://gitlab.ost.ch/damian.dasser/datajson/-/raw/main/ich_tanke_strom.geojson'
    r = requests.get(data_url)
    result = r.json()
    json_data = result['features']

    data = []
    processed_ids = []
    for el in json_data:
        lat = el['geometry']['coordinates'][1]
        lon = el['geometry']['coordinates'][0]

        el_prop = el['properties']
        station_id = el_prop['ref']

        tags = el_prop

        # Remove undesired tags
        tags.pop('@spider')  # irrelevant for OSM

        # TODO # bad quality. needs to be fixed in alltheplaces
        # Current examples:
        #   Querverbindung A13 2, Thusis 0, 0 Thusis
        #   Route de Dizy 2 0, 0 Cossonay
        #   Domplatz 8 / Domgasse 0, 0 Arlesheim
        #   Raststätte Würenlos, Richtung Bern 0, 0 Würenlos
        #   Pfingstweidstrasse 102 0, 0 8005 Zürich
        tags.pop('addr:full')

        if station_id in processed_ids:
            print(f'-- Shop {station_id} already present')
        else:
            processed_ids.append(station_id)
            # print(f"ID:{shop_id}, LAT:{lat}, LON:{lon}, TAGS:{tags}")

            # Class SourcePoint() will be available after this file was imported during execution
            data.append(SourcePoint(station_id, lat, lon, tags))

    return data
