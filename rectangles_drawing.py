import numpy as np
import math

def calculate_one_pixels_diffs(right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon, img_cutted_shape):
    """
    Возвращает разницу в lat на 1 пиксель и разницу в lon на 1 пиксель для обрезанной картинки
    """
    return (abs((left_bottom_lat - right_top_lat) / img_cutted_shape[0]),
        abs((right_top_lon - left_bottom_lon) / img_cutted_shape[1]))


def draw_rectangle_for_element_idx(idx, bounds, img_cutted, color_rgb_code,
                                  right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                                  one_pixel_lat_diff, one_pixel_lon_diff):
    
    bounds_cur = bounds[idx]
#     print(bounds_cur)
    maxlat_cur = bounds_cur['maxlat']
    maxlon_cur = bounds_cur['maxlon']
    minlat_cur = bounds_cur['minlat']
    minlon_cur = bounds_cur['minlon']
    
    minlat_cur_pixel = img_cutted.shape[0] - int(round((minlat_cur - left_bottom_lat) / one_pixel_lat_diff, 0))
    maxlat_cur_pixel = int(round((right_top_lat - maxlat_cur) / one_pixel_lat_diff, 0))

    minlon_cur_pixel = int(round((minlon_cur - left_bottom_lon) / one_pixel_lon_diff, 0))
    maxlon_cur_pixel = img_cutted.shape[1] - int(round((right_top_lon - maxlon_cur) / one_pixel_lon_diff, 0))
    
#     print("maxlat:", maxlat_cur_pixel)
#     print("minlat:", minlat_cur_pixel)
    
    img_cutted_shape = img_cutted.shape
    maxlat_cur_pixel = np.clip(maxlat_cur_pixel, 0, img_cutted_shape[0] - 1)
    minlat_cur_pixel = np.clip(minlat_cur_pixel, 0, img_cutted_shape[0] - 1)
        
#     print("minlon:", minlon_cur_pixel)
#     print("maxlon:", maxlon_cur_pixel)
    
    maxlon_cur_pixel = np.clip(maxlon_cur_pixel, 0, img_cutted_shape[1] - 1)
    minlon_cur_pixel = np.clip(minlon_cur_pixel, 0, img_cutted_shape[1] - 1)
    
#     print(maxlat_cur_pixel, minlat_cur_pixel, maxlon_cur_pixel, minlon_cur_pixel)
    
    if minlat_cur_pixel != maxlat_cur_pixel and minlon_cur_pixel != maxlon_cur_pixel\
        and (minlat_cur_pixel - maxlat_cur_pixel) > img_cutted.shape[0] * 0.01\
        and (maxlon_cur_pixel - minlon_cur_pixel) > img_cutted.shape[1] * 0.01\
        and (minlat_cur_pixel - maxlat_cur_pixel) < img_cutted.shape[0] * 0.99\
        and (minlat_cur_pixel - maxlat_cur_pixel) < img_cutted.shape[1] * 0.99:
    
#         print("Going to show")
    
        for i in range(maxlat_cur_pixel, minlat_cur_pixel):
            img_cutted[i, minlon_cur_pixel] = color_rgb_code
            img_cutted[i, maxlon_cur_pixel] = color_rgb_code

        for i in range(minlon_cur_pixel, maxlon_cur_pixel):
            img_cutted[minlat_cur_pixel, i] = color_rgb_code
            img_cutted[maxlat_cur_pixel, i] = color_rgb_code
            
#         print()

    return img_cutted

def draw_all_rectangles(img_cutted, bounds, tags, right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                       one_pixel_lat_diff, one_pixel_lon_diff):
    img_new = img_cutted.copy()
    
    for i in range(len(tags)):
        if tags[i] == 'wood':
            print(i, "wood")
            img_new = draw_rectangle_for_element_idx(i, bounds, img_new, [255, 0, 0],
                                                    right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                                                    one_pixel_lat_diff, one_pixel_lon_diff)
        if tags[i] == 'water':
            print(i, "water")
            img_new = draw_rectangle_for_element_idx(i, bounds, img_new, [0, 0, 255],
                                                    right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                                                    one_pixel_lat_diff, one_pixel_lon_diff)
        if tags[i] == 'peak':
            print(i, "peak")
            img_new = draw_rectangle_for_element_idx(i, bounds, img_new, [0, 255, 255],  # желтый
                                                    right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                                                    one_pixel_lat_diff, one_pixel_lon_diff)
        if tags[i] == 'valley': # долина
            print(i, "valley")
            img_new = draw_rectangle_for_element_idx(i, bounds, img_new, [128, 0, 255], 
                                                    right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                                                    one_pixel_lat_diff, one_pixel_lon_diff)
        if tags[i] == 'ridge':  # хребет
            print(i, "ridge")
            img_new = draw_rectangle_for_element_idx(i, bounds, img_new, [20, 255, 57],  
                                                    right_top_lat, right_top_lon, left_bottom_lat, left_bottom_lon,
                                                    one_pixel_lat_diff, one_pixel_lon_diff)
            
    return img_new