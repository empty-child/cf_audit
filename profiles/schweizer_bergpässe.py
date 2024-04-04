"""
Profile for Swiss Peaks
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
source = 'https://www.swisstopo.admin.ch/de/landschaftsmodell-swissnames3d'

# '''
# Tags for querying with overpass api
# '''
query = [('natural', 'saddle')] #[mountain_pass=yes]'

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm
# '''
master_tags = ('name', 'ele')

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
duplicate_distance = 10

# '''
# Use bbox from dataset points (default). False = query whole world, [minlat, minlon, maxlat, maxlon] to override
# restrict bounding box, makes query much, much faster!
# '''
bbox = True #[45.6755, 5.7349, 47.9163, 10.6677]

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
    import csv
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326")
    

    data = []
    processed_ids = []
    
    with open('./csv/swissNAMES3D_PKT.csv', mode='r') as csv_file:
        csv_dict = csv.DictReader(csv_file, delimiter=';')
        for element in csv_dict:
            if element['OBJEKTART'] in ['Pass',]:

                el_prop = {
                    'name': element['NAME'],
                    'ele': element['HOEHE'],
                    'natural': 'saddle', 
                }
                
                
                lat, lon = transformer.transform(element['E'], element['N'])


                tags = el_prop

                shop_id = element['NAME_UUID']

                if shop_id in processed_ids:
                    #print(f'-- Shop {shop_id} already present')
                    continue
                else:
                    processed_ids.append(shop_id)

                    # Class SourcePoint() will be available after this file was imported during execution            
                    data.append(SourcePoint(shop_id, lat, lon, tags))
    return data
