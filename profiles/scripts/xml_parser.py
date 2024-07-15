import xml.etree.ElementTree as ET
import json

geojson = {"type" : "FeatureCollection"}
features = []

toBeRemoved = []

tree = ET.parse('../mapped_paesse.xml')
root=tree.getroot()
for child in root.findall('node'):
    entry = {"type" : "Feature", "properties" : {}, "geometry" : {"type" : "Point", "coordinates" : [float(child.attrib['lon']), float(child.attrib['lat'])]}}
    for tags in child.findall('tag'):
        if tags.attrib['k'] and tags.attrib['k'] == 'name':
            entry["properties"]['name'] = tags.attrib['v']
            if 'pass' in tags.attrib['v'] or 'passo' in tags.attrib['v'] or 'col' in tags.attrib['v']:
                features.append(entry)
                toBeRemoved.append(child)
        elif tags.attrib['k']:
            entry['properties'][tags.attrib['k']] = tags.attrib['v']       



for remove in toBeRemoved:
    root.remove(remove)
    print("removed")

tree.write('filtered_paesse.osm')


geojson['features'] = features


with open('data.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=4)


