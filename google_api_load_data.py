import numpy as np
import requests
import cv2
import math

from utils import calculate_right_top_coordinates
URL = "https://maps.googleapis.com/maps/api/staticmap?"

DELTA_LAT_PIX = 300
DELTA_LON_PIX = 400

K_LAT = 730.7543613843219
K_LON = 728.2110091743106

DELTA_LON_FIX = DELTA_LON_PIX / K_LON


def load_and_prepare_image_by_url(url, tmp_filename):
    r = requests.get(url)
    with open(tmp_filename, 'wb') as f:
        f.write(r.content) 
        
    return cv2.imread(tmp_filename).astype(np.uint8)


def load_plain_image(center, is_debug=False, tmp_filename="tmp_orig.png"):
    """
    Загружает обычное изображение карты из google maps с центром в точке center
    Пример параметра: center = "54.52805,49.3291"
    """
    request_url = URL + "center=" + center + "&zoom=10&size=600x600&key=" + API_KEY + "&sensor=false"
    if is_debug:
        print(request_url)
    return load_and_prepare_image_by_url(request_url, tmp_filename)
        

def load_image_with_markers(center, marker_left_bottom, marker_right_top, tmp_filename="tmp_with_markers.png"):
    """
    Загружает обычное изображение из карты google maps с центром в точке center и маркерами в точках
    marker_left_bottom, marker_right_top
    Маркеры отвечают за границы требуемого изображение, про которое получена информация из openStreetMaps
    
    Примеры передаваемых параметров:
    center = "54.52805,49.3291"
    marker_left_bottom = "54.4081,48.9805"
    marker_right_top = "54.6480,49.6781"
    """
    request_url = (URL + "center=" + center + "&zoom=10&size=600x600&key=" + API_KEY + "&sensor=false"
                     +"&markers=color:blue%7Clabel:L%7C" + marker_left_bottom
                     +"&markers=color:blue%7Clabel:R%7C" + marker_right_top)
    return load_and_prepare_image_by_url(request_url, tmp_filename)


def load_satellite_image(center, tmp_filename="tmp_orig_satellite.png"):
    """
    Загружает из google maps изображение со спутника с центром в точке center, без маркеров
    """
    request_url = URL + "center=" + center + "&zoom=10&size=600x600&key=" + API_KEY + "&sensor=false&maptype=satellite"
    return load_and_prepare_image_by_url(request_url, tmp_filename)


def load_all_images(center, marker_left_bottom, marker_right_top, is_debug=False):
    img_plain = load_plain_image(center, is_debug=is_debug)
    img_with_markers = load_image_with_markers(center, marker_left_bottom, marker_right_top)
    img_satellite = load_satellite_image(center)
    
    return img_plain, img_with_markers, img_satellite


def find_borders_and_cut_img(img_orig, img_with_markers, img_satellite, is_debug=False, filename_diff="tmp_diff.png",
                            filename_grey="tmp_grey.png", filename_cutted_orig="tmp_cutted_orig.png",
                            filename_cutted_satellite="tmp_cutted_satellite.png"):
    """
    Используя картинку с маркерами определяет используемые границы изображения, возвращает картинку, обрезанную по этим границам
    """
    img_diff = cv2.medianBlur(np.absolute(img_with_markers - img_orig).astype(np.uint8), 5)
    if is_debug:
        cv2.imwrite(filename_diff, img_diff)
    
    img_grey = img_diff.mean(axis=2)
    if is_debug:
        cv2.imwrite(filename_grey, img_grey)
    
    def find_bottom(img_grey, start_height, img_diff):
        # Поднимаемся наверх по изображению, находим первую не чёрную точку - это маркер
        for i in range(start_height)[::-1]:
            for j in range(img_grey.shape[1]):  
                if img_grey[i][j] > 1 and \
                    (((img_diff[i][j][2] > img_diff[i][j][0]) and (img_diff[i][j][1] > img_diff[i][j][0])) \
                    or (img_diff[i][j][0] == 0 and img_diff[i][j][2] != 255)):   
                    if is_debug:
                        print(img_diff[i][j])
                        print(img_grey[i][j])
                    return (i, j)
                
    # Поиск левой нижней границы
    i, j = find_bottom(img_grey, img_grey.shape[0], img_diff)
    if is_debug:
        print(i, j)
    # Поиск правой верхней границы
    k, m = find_bottom(img_grey, img_grey.shape[0] // 2, img_diff)
    if is_debug:
        print(k, m)
    img_diff[i-2, j] = [0, 0, 255]  # Сдвиг -2, чтобы точка была ближе к середине кончика маркера
    img_diff[k-2, m] = [0, 0, 255]
    
    # Если что-то пошло немного не так, нужно поправить размеры картинки
    def correct_image_sizes(i, k, delta_should_be):
        delta = i - k
        
        if delta > delta_should_be:  # Получилось чуть-чуть многовато -> обрезать
            extra_pixels = delta - delta_should_be
            if extra_pixels > 4:
                raise Exception("is too big, has extra pixels:", extra_pixels)
            if extra_pixels % 2 == 0:
                k = k + (extra_pixels / 2)
                i = i - (extra_pixels / 2)
            else:
                k = k + (extra_pixels - int(extra_pixels / 2))
                i = i - int(extra_pixels / 2)
        
        if delta < delta_should_be:  # Получилось чуть-чуть маловато -> добавить
            lack_pixels = delta_should_be - delta
            if lack_pixels > 4:
                raise Exception("is too small, lack of pixels:", lack_pixels)
            if lack_pixels % 2 == 0:
                k = k - (lack_pixels / 2)
                i = i + (lack_pixels / 2)
            else:
                k = k - (lack_pixels - int(lack_pixels / 2))
                i = i + int(lack_pixels / 2)
                
        return i, k
    
    if is_debug:
        print("lat:", (i - 2) - (k - 2))
    i, k = correct_image_sizes(i, k, DELTA_LAT_PIX)
    if is_debug:
        print("lon:", m - j)
    m, j = correct_image_sizes(m, j, DELTA_LON_PIX)
    
    # Теперь можно обрезать оригинальную картинку
    img_cutted = img_orig[(k - 2):(i - 2), j:m]
    if is_debug:
        cv2.imwrite(filename_cutted_orig, img_cutted)
    
    # И картинку со спутника
    img_cutted_satellite = img_satellite[(k - 2):(i - 2), j:m]
    if is_debug:
        cv2.imwrite(filename_cutted_satellite, img_cutted_satellite)
    
    return img_cutted, img_cutted_satellite


# Полноценная загрузка одной картинки
def load_prepare_and_cut_image(left_bottom_lat, left_bottom_lon, is_debug=False, return_satellite=True):
    # TODO: запуск этой функции надо, наверное, отсюда вынести
    right_top_lat, right_top_lon = calculate_right_top_coordinates(left_bottom_lat, left_bottom_lon)
    center = [(right_top_lat + left_bottom_lat) / 2, (right_top_lon + left_bottom_lon) / 2]
    
    center_str = ','.join(map(str, center))
    marker_right_top = ','.join(map(str, [right_top_lat, right_top_lon]))
    marker_left_bottom = ','.join(map(str, [left_bottom_lat, left_bottom_lon]))
    
    img_plain, img_with_markers, img_satellite = load_all_images(center_str, marker_left_bottom, marker_right_top,
                                                                 is_debug=is_debug)
    img_cutted, img_cutted_satellite = find_borders_and_cut_img(img_plain, img_with_markers, img_satellite, is_debug=is_debug)
    
    if return_satellite:
        return img_cutted_satellite
    return img_cutted
