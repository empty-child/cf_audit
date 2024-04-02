import json


f = open("preview.json", encoding='utf-8')


data = json.load(f)

deleted = 0

index = 0
while index < len(data['features']):
    i = data['features'][index]
    if i['properties']:
        y = i['properties']
        if 'tags_changed.ele' in y:
            elevation = (i['properties']['tags_changed.ele'])

            values = elevation.split(' ')

            if ((float(values[0]) - float(values[2])) < 5):
                deleted = deleted + 1
                i['properties']['tags.ele'] = str(values[0])

                del i['properties']['tags_changed.ele']

                keys = i['properties'].keys()
                changeTagCount = 0

                for key in keys:
                    if 'tags_changed' in key:
                        changeTagCount = 1
                
                if changeTagCount == 0:
                    del data['features'][index]
                else:
                    index = index + 1
            else:
                index = index + 1
        else:
            index = index + 1
    else:
        index = index + 1
                    


with open('aplenjson.json', 'w') as outfile:
    json.dump(data, outfile)



