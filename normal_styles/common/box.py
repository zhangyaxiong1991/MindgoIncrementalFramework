# -*- coding: utf-8 -*- 
# @Time : 2020/1/14 0014 下午 10:56 
# @Author : Maton Zhang 
# @Site :  
# @File : box.py 
from normal_styles.base import BaseStyle


class CommonBox001(BaseStyle):
    LOW = -1
    HIGH = 1

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.step = kwargs['step']
        self.start = pd._libs.tslib.Timestamp(kwargs['start'])
        self.end = pd._libs.tslib.Timestamp(kwargs['end'])
        self.low_points_range = [[pd._libs.tslib.Timestamp(i[0]), pd._libs.tslib.Timestamp(i[1])] for i in kwargs['low_points_range']]
        self.high_points_range = [[pd._libs.tslib.Timestamp(i[0]), pd._libs.tslib.Timestamp(i[1])] for i in kwargs['high_points_range']]

    def set_data(self, stock_data, style_data, result_data):
        low_points = []
        for low_range in self.low_points_range:
            low_point_date = self.get_min_index(stock_data['low'], low_range)
            if low_point_date is None:
                continue
            low_points.append([low_point_date, stock_data.loc[low_point_date]['low'], self.LOW])

        high_points = []
        for high_range in self.high_points_range:
            high_point_date = self.get_max_index(stock_data["high"], high_range)
            if high_point_date is None:
                continue
            high_points.append([high_point_date, stock_data.loc[high_point_date]['high'], self.HIGH])

        points = low_points + high_points
        points.sort(key=lambda x: x[0])

        i = 0
        length = (len(points) -1)
        while i < length:
            point = points[i]
            next_point = points[i + 1]
            if point[2] * next_point[2] < 0:
                i += 1
                continue
            if point[2] == self.HIGH:
                if next_point[1] > point[1]:
                    points[i] = next_point
            else:
                if next_point[1] < point[1]:
                    points[i] = next_point
            # 删除已合并的值，且不向后推进，继续合并
            points.pop(i + 1)
            length = (len(points) -1)

        i = 0
        lines = []
        while i < (len(points) -1):
            line = [points[i], points[i+1], points[i+1][2], abs(points[i+1][1] - points[i][1]), abs(points[i+1][1] - points[i][1]) / points[i][1]]
            lines.append(line)
            i += 1

        i = 0
        while i < (len(lines) -1):
            l1 = lines[i]
            l2 = lines[i + 1]
            if abs((l2[3] - l1[3]) / l1[3]) > 0.382:
                result_data['error'] = "not box line1: {}. line2: {}".format(l1, l2)
            i += 1

        result_data['high'] = max([i[1] for i in points])
        result_data['low'] = min([i[1] for i in points])
        result_data['start'] = points[0][0]
        result_data['end'] = points[-1][0]
