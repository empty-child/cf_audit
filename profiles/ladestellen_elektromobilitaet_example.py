# **WARNING**: this example isn't complete, 
# and should really only be used as an example!

# Where to get the latest feed
download_url = 'https://data.geo.admin.ch/ch.bfe.ladestellen-elektromobilitaet/data/oicp/ch.bfe.ladestellen-elektromobilitaet.json'

# What will be put into "source" tags.
source = 'https://opendata.swiss/de/dataset/ladestationen-fuer-elektroautos/resource/e33957be-180a-422b-90a5-fbfe9774927a'

# A fairly unique id of the dataset to query OSM, used for "ref:mos_parking" tags
# If you omit it, set explicitly "no_dataset_id = True"
dataset_id = 'ch.bfe.ladestellen-elektromobilitaet:chargingstationid'
# no_dataset_id = True
# Tags for querying with overpass api
query = [('amenity', 'charging_station'),]
# Use bbox from dataset points (default). False = query whole world, [minlat, minlon, maxlat, maxlon] to override
bbox = True
# How close OSM point should be to register a match, in meters. Default is 100
# for chargingstations this can be very close together, but something like 10 meters leads to multiple new points, 
# that should acually be duplicates.
# this issue should be looked into further for non-example datasets, and might need some adaptations for each dataset
max_distance = 100
# Delete objects that match query tags but not dataset? False is the default
delete_unmatched = False
# If set, and delete_unmatched is False, modify tags on unmatched objects instead
# Always used for area features, since these are not deleted
tag_unmatched = {
    'fixme': 'Possibly removed charging station.',
    'amenity': None,
    'was:amenity': 'charging_station'
}
# Actually, after the initial upload we should not touch any existing non-matched objects
tag_unmatched = None
# A set of authoritative tags to replace on matched objects
# 'note', 'note', 'note', 'addr:street', 'addr:housenumber', 'source', 'website'
# 'note:en', 'note:de', 'note:fr', 'note:it', 'addr:city', 'addr:postcode'
master_tags = ('capacity', 'name', 'operator', 'source', 'ref')

# increase overpass timeout for large datasets!
overpass_timeout = 10000
# restrict boundung box, makes query much much faster!
# this is Switzerland's bbox!
bbox = [45.7309, 5.8509, 47.8443, 10.5805]

# A list of SourcePoint objects. Initialize with (id, lat, lon, {tags}).
def dataset(fileobj):
    # by the way the import happens, all imports and functions must be defined inside this function!
    import json
    import requests

    # special function to parse this rather strange format
    def get_from_json(json_in, mapping):
        evse_data = json_in['EVSEDataRecord']
        res = []
        for entry in evse_data:
            try:
                e = {}
                for osm_key, extractor in mapping.items():
                    if callable(extractor):
                        e[osm_key] = extractor(entry)
                    elif value := entry.get(extractor, None):
                        e[osm_key] = value
                res.append(e)
            except Exception as e:
                print(entry)
                print(extractor, )
                print(osm_key)
                raise
        return res

    DATA_PATH = 'https://data.geo.admin.ch/ch.bfe.ladestellen-elektromobilitaet/data/oicp/ch.bfe.ladestellen-elektromobilitaet.json'
    r = requests.get(DATA_PATH)
    result = r.json()
    json_data = result['EVSEData']
    
    # this isn't complete, and should really only be used as an example!
    # see here: https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dcharging_station for what could also be extracted
    # this is a mapping for osm_keys to whatever comes in from the json
    keys_mapping = {
        # this ref is needed for automated imports and such. Just as an example. Is being removed down below again
        'ref:ch.bfe.ladestellen-elektromobilitaet:chargingstationid': 'ChargingStationId',
        'lat': lambda x: float(x['GeoCoordinates']['Google'].split(' ')[0]),
        'lon': lambda x: float(x['GeoCoordinates']['Google'].split(' ')[1]),
        'addr:city': lambda x: x['Address']['City'],
        'addr:country': lambda _: 'Switzerland',
        'addr:postcode': lambda x: x['Address']['PostalCode'],
        'addr:street': lambda x: x['Address']['Street'],
        'addr:housenumber': lambda x: x['Address']['HouseNum'],
    }
    data = []
    processed_ids = []
    for el in json_data:
        stations = get_from_json(el, keys_mapping)
        for station_tags in stations:
            lat = station_tags.pop('lat')
            lon = station_tags.pop('lon')
            # this ref is for better matching (ie. automated imports into OSM) and such.
            # Probably not needed in other examples, therefore removed from tags
            station_id = station_tags.pop('ref:ch.bfe.ladestellen-elektromobilitaet:chargingstationid')
            if station_id in processed_ids:
                print(f'{station_id} already present')
                continue
            processed_ids.append(station_id)
            print(station_tags)
            data.append(SourcePoint(station_id, lat, lon, station_tags))
    return data
