"""
Profile for Winterthurer Spielplaete

Date: 2023-08-30
Author: OST
License: MIT
"""

# '''
# Where to get the latest feed
# '''
download_url = 'https://stadtplan.winterthur.ch/wfs/SitzbankWfs?VERSION=1.0.0&SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:SitzbankWfs'

# '''
# What will be put into "source" tags.
# '''
source = 'https://alltheplaces.xyz'

# '''
# Tags for querying with overpass api
# '''
query = [('amenity', 'bench'),]

# '''
# A set of tags, which are more trustworthy from the external source than the ones from OSM
# This is only for faster validation by a user (preselected radio button).
# It does not influence the matching algorithm
# '''
master_tags = ('ref', 'inscription',)

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
duplicate_distance = -1
#TODO: Adjust

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
    import xml.etree.ElementTree as ET
    import requests
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326")

    name_spaces = {'owl' : 'http://www.opengis.net/wfs','gml' : 'http://www.opengis.net/gml', 'ms' : 'http://mapserver.gis.umn.edu/mapserver'}

    data_url = 'https://stadtplan.winterthur.ch/wfs/SitzbankWfs?VERSION=1.0.0&SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:SitzbankWfs'
    r = requests.get(data_url)

    root = ET.fromstring(r.content)

    data = []
    processed_ids = []
    
    for element in root.findall('gml:featureMember', name_spaces):
        el_data = element[0]

        shop_id = int(el_data.find('ms:Banknummer', name_spaces).text)


        # banktyp always lower
        banktyp = str(el_data.find('ms:Banktyp', name_spaces).text).lower()

        if not 'halbling-tisch' in banktyp:

            material = 'wood' if 'holz' in banktyp else None
            colour = 'red' if 'rot' in banktyp else 'gray' if 'grau' in banktyp else None
            backrest = 'yes' if 'mit lehne' in banktyp else 'no' if 'ohne lehne' in banktyp else None

            el_prop = {
                'amenity' : 'bench',
                'operator:wikidata' : 'Q56825906',
                'ref' : shop_id,
                'inscription' : el_data.find('ms:Widmung', name_spaces).text,
                'note' : el_data.find('ms:Standort', name_spaces).text,
                'material' : material,
                'colour' : colour,
                'backrest' : backrest
            }



            geometry = el_data.find('ms:msGeometry', name_spaces).find('gml:Point', name_spaces).find('gml:coordinates', name_spaces).text

            # Not all entries have geometry set
            if geometry != '' or geometry == None:
                x, y = str(geometry).split(',')


                lat, lon = transformer.transform(x, y)
            else:
                print(f'-- NO GEOMETRY for {shop_id}')

            tags = el_prop


            if shop_id in processed_ids:
                print(f'-- Shop {shop_id} already present')
            else:
                processed_ids.append(shop_id)

                # Class SourcePoint() will be available after this file was imported during execution
                data.append(SourcePoint(shop_id, float(lat), float(lon), tags))


    return data
