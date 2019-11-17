from osm_object import calculate_border_angles_to_object_and_point, calculate_osm_object_center
from osm_object import One_OSM_object, Image_OSM_object
from utils import calculate_distance

import math
import numpy as np

# fast diagram
from diagram import Diagram

class Circle_diagram(object):
    def __init__(self, sectors_count, center_point, img_shape):
        self.sectors_count = sectors_count
        self.center_point = center_point
        self.img_shape = img_shape
    
        # Количество градусов, которое помещается в каждом секторе
        self.step_grad = 360 / sectors_count
        
        self.sectors = [[] for _ in range(sectors_count)]
        
    def insert(self, osm_object):
        center_x = self.center_point[0]
        center_y = self.center_point[1]
        
        angle_1, angle_2 = calculate_border_angles_to_object_and_point(center_x, center_y, osm_object, self.img_shape)
        
### почему???
#         angle_1, angle_2 = calculate_border_angles_to_object_and_point(center_y, center_x, osm_object, self.img_shape)
        object_x, object_y = calculate_osm_object_center(osm_object)
        
        distance = calculate_distance((center_x, center_y), (object_x, object_y))
### почему???
#         distance = calculate_distance((center_x, center_y), (object_y, object_x))
        
        diff_between_angles = abs(angle_2 - angle_1)
        # Перехода через 0 нет
        start_angle = min(angle_1, angle_2)
        end_angle = max(angle_1, angle_2)
            
        if diff_between_angles >= 180: # Есть переход через 0
            start_angle = max(angle_1, angle_2)
            end_angle = min(angle_1, angle_2)
            
        sector_start_idx = int(start_angle / self.step_grad)
        sector_end_idx = int(end_angle / self.step_grad)
        
        if diff_between_angles < 180:
            for sector_idx in range(sector_start_idx, sector_end_idx + 1):    
                self.sectors[sector_idx].append((distance, osm_object.tag))
        else:
            for sector_idx in list(range(sector_start_idx, self.sectors_count)) + list(range(0, sector_end_idx)):
                self.sectors[sector_idx].append((distance, osm_object.tag))
        
    def resort_sectors(self):
        """
        Упорядочевает объекты внутри сектора по степени увеличения расстояния до объекта
        """
        for i in range(len(self.sectors)):
            self.sectors[i] = sorted(self.sectors[i])
            
    def rotate(self):
        """
        'Поворачивает' диаграмму на 1 сектор
        """
        self.sectors = [self.sectors[-1]] + self.sectors[:-1]        
                    
            
    def make_fast(self):
        """
        Быстрая версия секторов, написанная на cython
        """
        self.fast_diagram = Diagram(self.sectors)
        
        
def create_circle_diagram(sectors_count, center_point, img_osm):
    cd = Circle_diagram(sectors_count, center_point, img_osm.img_cutted_shape)
    
    for i in range(len(img_osm.osm_objects)):
        osm_object = img_osm.osm_objects[i]
        cd.insert(osm_object)
    
    cd.resort_sectors()
    return cd            


def calculate_angle_by_blocks_count(t):
    """
    t - количество блоков на большей стороне изображения
    (см формулы, там это обозначается именно как t)
    
    Возвращает угол сектора круговой диаграммы В ГРАДУСАХ
    """
    t_sq_d = 1 / (t ** 2)
    numerator = 2 * t_sq_d / 4 + t_sq_d * (t - 3 / 2) ** 2 - t_sq_d + (1 - 1 / (2 * t)) ** 2
    denominator = 1 / t * math.sqrt(1 + 4 * (t - 3 / 2) ** 2) * math.sqrt(t_sq_d / 4 + (1 - 1 / (2 * t)) ** 2)
    return math.degrees(math.acos(numerator / denominator))


def calculate_blocks_centers(img_osm_shape, bigger_size_blocks_count):
    """
    Определяет координаты центров элементов сетки на изображении в пикселях
    """
    height, width, _ = img_osm_shape
    
    bigger_side_len = height
    if width > bigger_side_len:
        bigger_side_len = width
    
    # Большая сторона должна делиться на количество элементов нацело
    one_element_len = bigger_side_len / bigger_size_blocks_count
    assert(one_element_len % 1 == 0)
    one_element_len = int(one_element_len)
    
    assert((height / one_element_len) % 1 == 0)
    assert((width / one_element_len) % 1 == 0)
    
    blocks_count_height = int(height / one_element_len)
    blocks_count_width = int(width / one_element_len)
    
    
    height_dots = []
    width_dots = []
    
    for i in range(blocks_count_height):
        height_dots.append(i * one_element_len + one_element_len / 2)
    for i in range(blocks_count_width):
        width_dots.append(i * one_element_len + one_element_len / 2)
    
#     # Этот блок кода отвечает за перекрывающиеся элементы сетки
#     for i in range(1, blocks_count_height):
#         height_dots.append(one_element_len * i)
#     for i in range(1, blocks_count_width):
#         width_dots.append(one_element_len * i)
    
    center_points = []
    for i in range(len(height_dots)):
        for j in range(len(width_dots)):
            center_points.append((height_dots[i], width_dots[j]))
            
    return center_points


def calculate_sectors_count(bigger_side_blocks_count):
    sector_angle = calculate_angle_by_blocks_count(bigger_side_blocks_count)
    # Округляем вверх, чтобы наверняка гарантировать точность
    return math.ceil(360. / sector_angle)


class Image_circle_diagrams(object):
    def __init__(self, img_osm, bigger_side_blocks_count, sectors_count, with_fast=True):
        """
        img_osm - структура объектов на изображении (см utils)
        bigger_size_blocks_count - количество элементов сетки на большей стороне изображения
        """
        self.sectors_count = sectors_count
        
        # Дальше нужно понять, сколько будет блоков всего на изображении, и где будут находиться центры этих блоков (сетки)
        self.center_points = calculate_blocks_centers(img_osm.img_cutted_shape, bigger_side_blocks_count)
        
        # Теперь для каждой из центральных точек нужно построить круговую диаграмму
        self.circle_diagrams = []
        if with_fast:
            self.fast_diagrams = []
            
        for center_p in self.center_points:
            circle_diagram = create_circle_diagram(self.sectors_count, center_p, img_osm)
            self.circle_diagrams.append(circle_diagram)
            
            if with_fast:
                self.fast_diagrams.append(Diagram(circle_diagram.sectors))
        
        
class Agent_circle_diagram(Circle_diagram):
    def __init__(self, sectors_count):
        self.sectors_count = sectors_count
    
        # Количество градусов, которое помещается в каждом секторе
        self.step_grad = 360 / sectors_count
        
        self.sectors = [[] for _ in range(sectors_count)]
    
    def insert(self, angle_1, angle_2, closeness_priority, tag):
        """
        Заметим следующее:
        объект может находиться, разумеется в нескольких секторах, в разных секторах у него может быть разный приоритет,
        например, у леса в одном секторе приоритет 1, а в другом 2
        В таком случае в круговую диаграмму добавляется несколько объектов, соответствующих одному на изображении:
        в приведённом выше примере будет добавлено 2 объекта - лес в одном секторе с приоритетом 1 и в другом с приоритетом 2
        
        angle_1 и angle_2 - значения в градусах
        closeness_priority - целое число от 1 до ..., чем дальше объект, тем выше closeness_priority
        tag - строка, тип объекта
        """
        diff_between_angles = abs(angle_2 - angle_1)
        if diff_between_angles < 180: # Перехода через 0 нет
            start_angle = min(angle_1, angle_2)
            end_angle = max(angle_1, angle_2)
            
        if diff_between_angles >= 180: # Есть переход через 0
            start_angle = max(angle_1, angle_2)
            end_angle = min(angle_1, angle_2)
            
        sector_start_idx = int(start_angle / self.step_grad)
        sector_end_idx = int(end_angle / self.step_grad)
        
        if diff_between_angles < 180:
            for sector_idx in range(sector_start_idx, sector_end_idx + 1):    
                self.sectors[sector_idx].append((closeness_priority, tag))
        else:
            for sector_idx in list(range(sector_start_idx, self.sectors_count)) + list(range(0, sector_end_idx)):
                self.sectors[sector_idx].append((closeness_priority, tag))
        
        
def calculate_penalty_for_sectors(sector_img_diagram, sector_agent_diagram):
    """
    Принимает по одному сектору из каждой диаграммы
    sector_img_diagram - сектор одной из диаграмм для изображения
    sector_agent_diagram - сектор диаграммы агента
    Секторы должны соответствовать друг другу по порядку
    
    Каждый из секторов представляет собой список пар: (расстояние или приоритет, тип объекта)
    Считаем, что объекты внутри сектора уже отсортированы в порядке увеличения расстояния до них
    """
    
    min_length = min(len(sector_img_diagram), len(sector_agent_diagram))
    
    penalty = 0
    
    for i in range(min_length):
        indicator = 0
        if sector_img_diagram[i][1] != sector_agent_diagram[i][1]:
            indicator = 1
        penalty += (indicator / (i + 1) ** 2)
    
    more_sector_len = max(len(sector_img_diagram), len(sector_agent_diagram)) - min_length
    for i in range(min_length, min_length + more_sector_len):
        penalty += (1 / (i + 1) ** 2)
        
    return penalty


def calculate_penalty_for_diagrams(img_sectors, agent_sectors):
    """
    Итоговый штраф для пары диаграмм вычислается как сумма штрафов всех последовательных пар секторов
    Принимает список секторов одной из круговых диаграмм для изображения и круговой диаграммы агента
    
    Возвращает число с плавающей точкой - суммарный штраф для пары диаграмм
    """
    assert(len(img_sectors) == len(agent_sectors))
    
    penalty_sum = 0
    
    for i in range(len(img_sectors)):
        penalty_sum += calculate_penalty_for_sectors(img_sectors[i], agent_sectors[i])
        
    return penalty_sum


def select_minimum_penalty_element_grid(img_cds, agent_cd, use_fast=True):
    """
    img_cds - объект класса Image_circle_diagrams
    agent_cd - объект класса Agent_circle_diagram
    use_fast - использовать ли быстрый способ подсчёта расстояний
    """
    center_points = []
    penalties = []
    
    for i in range(len(img_cds.center_points)):
        center_point = img_cds.center_points[i]
        
        if use_fast:
            penalties.append(img_cds.fast_diagrams[i].dist_to(agent_cd.fast_diagram))
        else:
            img_cd = img_cds.circle_diagrams[i]
            cur_cd_penalties = []

            for j in range(len(agent_cd.sectors)):
                cur_cd_penalties.append(calculate_penalty_for_diagrams(img_cd.sectors, agent_cd.sectors))
                agent_cd.rotate()
            penalties.append(min(cur_cd_penalties))
            
        center_points.append(center_point)
    
    minimum_penalty = min(penalties)
    # Вернём список из всех центров элементов сетки, которым соответствует минимальный штраф
    
    center_points_minimum_penalty = []
    indices_minimum_penalty = []
    
    for i in range(len(penalties)):
        if penalties[i] == minimum_penalty:
            center_points_minimum_penalty.append(center_points[i])
            indices_minimum_penalty.append(i)
    
    return center_points_minimum_penalty, indices_minimum_penalty, penalties
