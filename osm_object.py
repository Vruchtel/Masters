import numpy as np

from utils import calculate_one_pixels_diffs, calculate_angle, calculate_directed_angle

class One_OSM_object(object):
    """
    Представляет границы одного объекта на изображении в пикселях
    """
    def __init__(self, maxlat, maxlon, minlat, minlon, tag):
        self.maxlat = maxlat
        self.maxlon = maxlon
        self.minlat = minlat
        self.minlon = minlon
        self.tag = tag
    
    def print_osm_object(self):
        print("maxlat: %d, minlat: %d, maxlon: %d, minlon: %d" % (self.maxlat, self.minlat, self.maxlon, self.minlon))
        
    def is_equal(self, another_osm_object):
        if (self.maxlat == another_osm_object.maxlat) and (self.minlat == another_osm_object.minlat)\
            and (self.maxlon == another_osm_object.maxlon) and (self.minlon == another_osm_object.minlon)\
            and (self.tag == another_osm_object.tag):
                return True
        return False

        
class Image_OSM_object(object):
    """
    Класс, умеющий получать из данных osm и хранить границы объектов на изображении в пикселях
    """
    
    def __init__(self, img_cutted_shape, right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon, bounds, tags):
        self.img_cutted_shape = img_cutted_shape
        self.right_top_lat = right_top_lat
        self.right_top_lon = right_top_lon
        self.left_bottom_lat = left_bottom_lat
        self.left_bottom_lon = left_bottom_lon
        self.one_pixel_lat_diff, self.one_pixel_lon_diff = calculate_one_pixels_diffs(right_top_lat, right_top_lon,
                                                                                      left_bottom_lat, left_bottom_lon,
                                                                                      img_cutted_shape)
        self.osm_objects = []
        for i in range(len(bounds)):
            cur_osm_object = self.calculate_pixel_bounds(bounds[i], tags[i])
            if cur_osm_object is not None:
                already_in = False
                for before_object in self.osm_objects:
                    if before_object.is_equal(cur_osm_object):
                        already_in = True
                if not already_in:
                    self.osm_objects.append(cur_osm_object)
                    
        
    def calculate_pixel_bounds(self, grads_bounds, tag):        
        maxlat_grads = grads_bounds['maxlat']
        maxlon_grads = grads_bounds['maxlon']
        minlat_grads = grads_bounds['minlat']
        minlon_grads = grads_bounds['minlon']
        
        minlat_pixel = self.img_cutted_shape[0] - int(round((minlat_grads - self.left_bottom_lat) / self.one_pixel_lat_diff, 0))
        maxlat_pixel = int(round((self.right_top_lat - maxlat_grads) / self.one_pixel_lat_diff, 0))
        minlon_pixel = int(round((minlon_grads - self.left_bottom_lon) / self.one_pixel_lon_diff, 0))
        maxlon_pixel = self.img_cutted_shape[1] - int(round((self.right_top_lon - maxlon_grads) / self.one_pixel_lon_diff, 0))
        
        maxlat_pixel = np.clip(maxlat_pixel, 0, self.img_cutted_shape[0] - 1)
        minlat_pixel = np.clip(minlat_pixel, 0, self.img_cutted_shape[0] - 1)
        maxlon_pixel = np.clip(maxlon_pixel, 0, self.img_cutted_shape[1] - 1)
        minlon_pixel = np.clip(minlon_pixel, 0, self.img_cutted_shape[1] - 1)
        
        if minlat_pixel != maxlat_pixel and minlon_pixel != maxlon_pixel\
            and (minlat_pixel - maxlat_pixel) > self.img_cutted_shape[0] * 0.01\
            and (maxlon_pixel - minlon_pixel) > self.img_cutted_shape[1] * 0.01\
            and (minlat_pixel - maxlat_pixel) < self.img_cutted_shape[0] * 0.99\
            and (minlat_pixel - maxlat_pixel) < self.img_cutted_shape[1] * 0.99:
            new_osm_object = One_OSM_object(maxlat_pixel, maxlon_pixel, minlat_pixel, minlon_pixel, tag)
            
            return new_osm_object
            
        return None
    
    
def calculate_border_angles_to_object_and_point(x, y, osm_object, img_shape):
    """
    Функция, вычисляющая для одного osm-объекта два угла, между которыми можно видеть объект, находясь в точке (x, y)
    """
    minlat = osm_object.minlat
    maxlat = osm_object.maxlat
    minlon = osm_object.minlon
    maxlon = osm_object.maxlon

    # Получаем 4 вектора для каждой угловой точки границы объекта
    v1 = (maxlat - x, minlon - y)
    v2 = (maxlat - x, maxlon - y)
    v3 = (minlat - x, minlon - y)
    v4 = (minlat - x, maxlon - y)
    
    # Для каждой пары векторов посчитаем угол между ними
    vectors = [v1, v2, v3, v4]
    angle_vector_pair = {}
    for i in range(4):
        for j in range(i, 4):
            if i != j:
                vector_1 = vectors[i]
                vector_2 = vectors[j]

                angle = abs(calculate_angle(vector_1, vector_2))
                angle_vector_pair[angle] = (i, j)
                
    # Теперь нужно определить, какие 2 вектора дают максимальный угол
    max_angle = max(angle_vector_pair)
    vector_pair = angle_vector_pair[max_angle]
    vector_1 = vectors[vector_pair[0]]
    vector_2 = vectors[vector_pair[1]]

    # Определяем угол между каждым из векторов и осью абсцисс, начинающейся в точке (x, y)
    abscissa = (0, img_shape[1] - y)
    
    angle_1 = calculate_directed_angle(abscissa, vector_1)
    angle_2 = calculate_directed_angle(abscissa, vector_2)
    
    return angle_1, angle_2 


def calculate_osm_object_center(osm_object):
    minlat = osm_object.minlat
    maxlat = osm_object.maxlat
    minlon = osm_object.minlon
    maxlon = osm_object.maxlon
    
    return (minlat - maxlat, maxlon - minlon)