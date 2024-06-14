import json


f = open("preview_paesse.json", encoding='utf-8')


data = json.load(f)

deleted = 0

index = 0
while index < len(data['features']):
    i = data['features'][index]
    
    if i['properties']:
        y = i['properties']
        if y['action'] == "modify":
            del data['features'][index]
        else:
            index = index + 1
    else:
        index = index + 1

                    
with open('filtered_paesse.json', 'w') as outfile:
    json.dump(data, outfile)



