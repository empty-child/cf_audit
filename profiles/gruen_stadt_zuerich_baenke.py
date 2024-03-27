"""
Profile for Winterthurer Spielplaete

Date: 2023-08-30
Author: OST
License: MIT
"""

# '''
# Where to get the latest feed
# '''
download_url = 'https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Sitzbankkataster_OGD?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=bankstandorte_ogd'

# '''
# What will be put into "source" tags.
# '''
source = 'https://data.stadt-zuerich.ch'

# '''
# Tags for querying with overpass api
# '''
query = [('amenity', 'bench'),]

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm
# '''
master_tags = ('ref', 'armrest', 'backrest', 'picnic_table')

# '''
# How close OSM point should be to register a match, in meters. Default is 100
# for electronics this can be very close together, but something like 10 meters leads to multiple new points,
# that should actually be duplicates.
# this issue should be looked into further for non-example datasets, and might need some adaptations for each dataset
# '''
max_distance = 10

# '''
# Dataset points that are closer than this distance (in meters) will be considered duplicates of each other.
# '''
duplicate_distance = 1
#TODO: Adjust

# '''
# Use bbox from dataset points (default). False = query whole world, [minlat, minlon, maxlat, maxlon] to override
# restrict bounding box, makes query much, much faster!
# '''
bbox = True

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
    import re

    data_url = 'https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Sitzbankkataster_OGD?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=bankstandorte_ogd'
    r = requests.get(data_url)
    result = r.json()
    json_data = result['features']

    data = []
    processed_ids = []
    for element in json_data:
        el_prop = element['properties']
        bench_id = el_prop['objid']

        # Not all entries have geometry set
        if 'geometry' in element:
            lat = element['geometry']['coordinates'][1]
            lon = element['geometry']['coordinates'][0]
        else:
            print(f'-- NO GEOMETRY for {bench_id}')

        if el_prop['sitzbankmodelle']:
            backrest = 'yes' if el_prop['sitzbankmodelle'] in ['mit Rückenlehne', 'mit Rückenlehne und 2 Armlehnen', 'mit Rückenlehne und Armlehne links', 'mit Rückenlehne und Armlehne rechts', 'ohne Rückenlehne'] else 'no' if 'ohne Rückenlehne' in el_prop['sitzbankmodelle'] else None
        else:
            backrest = None

        el_prop = {
            'amenity' : 'bench',
            'operator' : 'Grün Stadt Zürich',
            'operator:wikidata' : 'Q1551785',
            'ref' : bench_id,
            'backrest' : backrest
        }

        tags = el_prop


        if addr := el_prop.get("adresse"):
            tags["addr:full"] = f"{addr}, Zürich"
            if m := re.match(r"^(.+) (\d+\s?[a-kA-K]?)$", addr):
                tags["addr:street"] = m.group(1)
                tags["addr:housenumber"] = m.group(2)

        if bench_id in processed_ids:
            print(f'-- Farm store {bench_id} already present')
        else:
            processed_ids.append(bench_id)

            # Class SourcePoint() will be available after this file was imported during execution
            data.append(SourcePoint(bench_id, lat, lon, tags))

    return data