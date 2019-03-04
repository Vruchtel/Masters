import math

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