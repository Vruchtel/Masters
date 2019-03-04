import requests
import json
import numpy as np


def load_data_from_openstreetmap(left_bottom_lat, left_bottom_lon, right_top_lat, right_top_lon, outfile_name):
#     overpass_url = "http://lz4.overpass-api.de/api/interpreter"
#     overpass_url = "http://overpass.osm.ch/api/interpreter"
    overpass_url = "https://overpass.kumi.systems/api/interpreter"
    overpass_query = """
    [out:json];
    node
    ["natural"="water"]
    ({0}, {1}, {2}, {3});
    out center;
    way
    ["natural"="water"]
    ({0}, {1}, {2}, {3});
    out geom;
    relation
    ["natural"="water"]
    ({0}, {1}, {2}, {3});
    out geom;

    node
    ["natural"="wood"]
    ({0}, {1}, {2}, {3});
    out center;
    way
    ["natural"="wood"]
    ({0}, {1}, {2}, {3});
    out geom;
    relation
    ["natural"="wood"]
    ({0}, {1}, {2}, {3});
    out geom;

    node
    ["natural"="peak"]
    ({0}, {1}, {2}, {3});
    out center;
    way
    ["natural"="peak"]
    ({0}, {1}, {2}, {3});
    out geom;
    relation
    ["natural"="peak"]
    ({0}, {1}, {2}, {3});
    out geom;

    node
    ["natural"="valley"]
    ({0}, {1}, {2}, {3});
    out center;
    way
    ["natural"="valley"]
    ({0}, {1}, {2}, {3});
    out geom;
    relation
    ["natural"="valley"]
    ({0}, {1}, {2}, {3});
    out geom;

    node
    ["natural"="ridge"]
    ({0}, {1}, {2}, {3});
    out center;
    way
    ["natural"="ridge"]
    ({0}, {1}, {2}, {3});
    out geom;
    relation
    ["natural"="ridge"]
    ({0}, {1}, {2}, {3});
    out geom;
    """.format(left_bottom_lat, left_bottom_lon, right_top_lat, right_top_lon)

    response = requests.get(overpass_url, 
                            params={'data': overpass_query})

    if response.status_code == 200:
        data = response.json()
    else:
        raise(Exception("Error while loading data from OpenStreetMap"))

    with open(outfile_name, 'w') as outfile:
        json.dump(data, outfile)
    return


# Дальше можно загрузить json с описанием объектов и вытащить из него эти объекты
def find_objects_bounds(datafile_name, right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon):
    """
    Определяет границы объектов. Удаляет слишком маленькие, слишком большие и вложенные в другие объекты одного типа
    """
    with open(datafile_name) as json_data:
        data = json.load(json_data)
    
    bounds = []
    tags = []
    
    img_lat_diff = abs(right_top_lat - left_bottom_lat)
    img_lon_diff = abs(right_top_lon - left_bottom_lon)

    for element in data['elements']:
        
        if element['tags']['natural'] == 'ridge':
            print("RIDGE")
        
        el_type = element['type']
        if el_type == 'node':
            print(element)
            lat, lon = (element['lat'], element['lon'])
            maxlat = lat + 0.01 * img_lat_diff
            minlat = lat - 0.01 * img_lat_diff
            maxlon = lon + 0.01 * img_lon_diff
            minlon = lon - 0.01 * img_lon_diff
        else:
            el_bounds = element['bounds']
            maxlat, maxlon, minlat, minlon = (el_bounds['maxlat'], el_bounds['maxlon'], el_bounds['minlat'], el_bounds['minlon'])
        # Здесь нужно также проверить, что площать элемента не слишком маленькая или не слишком большая
        # Рассматривать объекты будем только в пределах картинки
        maxlat = np.clip(maxlat, left_bottom_lat, right_top_lat)
        minlat = np.clip(minlat, left_bottom_lat, right_top_lat)
        maxlon = np.clip(maxlon, left_bottom_lon, right_top_lon)
        minlon = np.clip(minlon, left_bottom_lon, right_top_lon)

        el_bounds = {'maxlat': maxlat, 'minlat': minlat, 'maxlon': maxlon, 'minlon': minlon}
        lat_diff, lon_diff = (abs(maxlat - minlat), abs(maxlon - minlon))
        # Слишком маленькие и слишком большие объекты добавлять не будем
        if lat_diff >= img_lat_diff * 0.001 and lon_diff >= img_lon_diff * 0.001 \
            and lat_diff <= img_lat_diff * 0.999 and lon_diff <= img_lon_diff * 0.999:
        
            bounds.append(el_bounds)
            tags.append(element['tags']['natural'])

    # Здесь отбираются контуры - показываются только контуры одного типа, не содержащиеся в других объектах
    cur_max_objects = []
    cur_tags = []
    for element_idx in range(len(bounds)):
        element = bounds[element_idx]
        tag = tags[element_idx]
        maxlat, maxlon, minlat, minlon = (element['maxlat'], element['maxlon'], element['minlat'], element['minlon'])
        
        is_to_append = True
        
        for cur_max_object_idx in range(len(cur_max_objects)):
            cur_max_object = cur_max_objects[cur_max_object_idx]
            maxlat_cur_max, maxlon_cur_max = (cur_max_object['maxlat'], cur_max_object['maxlon'])
            minlat_cur_max, minlon_cur_max = (cur_max_object['minlat'], cur_max_object['minlon'])
            
            # Проверим, не содержится ли текущий максимальный объект в новом element
            if maxlat_cur_max <= maxlat and minlat_cur_max >= minlat and maxlon_cur_max <= maxlon and minlon_cur_max >= minlon\
                and tag == cur_tags[cur_max_object_idx]:
                cur_max_objects[cur_max_object_idx] = element
                cur_tags[cur_max_object_idx] = tag
                is_to_append = False
        if is_to_append:
            cur_max_objects.append(element)
            cur_tags.append(tag)

    return cur_max_objects, cur_tags
