import math
import numpy as np

DELTA_LAT_PIX = 300
DELTA_LON_PIX = 400

K_LAT = 730.7543613843219
K_LON = 728.2110091743106

DELTA_LON_FIX = DELTA_LON_PIX / K_LON


def calculate_right_top_coordinates(left_bottom_lat, left_bottom_lon):
    right_top_lon = left_bottom_lon + DELTA_LON_FIX
    
    delta_lat = DELTA_LAT_PIX * math.cos(math.radians(left_bottom_lat)) / K_LAT
    right_top_lat = left_bottom_lat + delta_lat
    
    return right_top_lat, right_top_lon


def calculate_one_pixels_diffs(right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon, img_cutted_shape):
    """
    Возвращает разницу в lat на 1 пиксель и разницу в lon на 1 пиксель для обрезанной картинки
    """
    return (abs((left_bottom_lat - right_top_lat) / img_cutted_shape[0]),
        abs((right_top_lon - left_bottom_lon) / img_cutted_shape[1]))


def calculate_angle(vector_1, vector_2):
    scalar_product = np.dot(vector_1, vector_2)
    norm_1 = np.linalg.norm(vector_1)
    norm_2 = np.linalg.norm(vector_2) 
    return np.rad2deg(np.arccos(scalar_product / (norm_1 * norm_2)))


def calculate_directed_angle(vector_1, vector_2):
    
    angle = calculate_angle(vector_1, vector_2)
    
    pseudoscalar_product = vector_1[0] * vector_2[1] - vector_1[1] * vector_2[0]
    norm_1 = np.linalg.norm(vector_1)
    norm_2 = np.linalg.norm(vector_2) 
    dir_angle = np.rad2deg(np.arcsin(pseudoscalar_product / (norm_1 * norm_2)))
    
    if dir_angle < 0:
        angle = 360 - angle
    return angle    


def calculate_distance(point_1, point_2):
    """
    Определяет евклидово расстояние между двумя точками
    """
    x1, y1 = point_1
    x2, y2 = point_2

    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
