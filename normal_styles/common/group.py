# -*- coding: utf-8 -*- 
# @Time : 2020/1/19 0019 下午 7:33 
# @Author : Maton Zhang 
# @Site :  
# @File : group.py 

from normal_styles.base import BaseStyle


class Point(BaseStyle):
    def __init__(self, date, price, type, range):
        self.range = range
        self.type = type
        self.start = range[0]
        self.end = range[1]
        self.date = date
        self.price = price


class Line(BaseStyle):
    def __init__(self, p1, p2, type):
        self.p1 = p1
        self.p2 = p2
        self.type = type
        self.length = None
        self.p_length = None
        self.high = None
        self.low = None
        self.flush()

    def flush(self):
        self.high = max(self.p1.price, self.p2.price)
        self.low = min(self.p1.price, self.p2.price)
        self.length = abs(self.p2.price - self.p1.price)
        self.p_length = abs(self.p2.price - self.p1.price) / self.p1.price
        self.start = self.p1.start
        self.end = self.p2.end

    def one_line(self, line):
        large, small = (self, line) if self.length > line.length else (line, self)
        if (small.length / large.length) > 0.6:
            return True
        return False

    def merge_line(self, line):
        large, small = self, line if self.length > line.length else line, self
        self.type = large.tpye
        all_point = [large.p1, small.p1, large.p2, small.p2]
        all_point.sort(key=lambda x: x.price)
        if self.type == self.HIGH:
            self.p1 = all_point[0]
            self.p2 = all_point[-1]
        else:
            self.p1 = all_point[-1]
            self.p2 = all_point[0]

    def merge_lines(self, lines):
        i = len(lines) - 1
        while i > 1:
            pre_line = lines[i]
            p_pre_line = lines[i - 1]
            if self.one_line(pre_line) and pre_line.one_line(p_pre_line):
                self.merge_line(pre_line)
                self.merge_line(p_pre_line)
                lines = lines[:i-1]
                i = len(lines) - 1
            break
        return lines


class Box(BaseStyle):
    def __init__(self, l1, l2):
        self.lines = [l1, l2]

        self.start = None
        self.end = None
        self.high = None
        self.low = None

        self.flush()

    def flush(self):
        self.start = self.left.start
        self.end = self.right.end
        self.high = max([i.high for i in self.lines])
        self.low = min(i.low for i in self.lines)

    @property
    def left(self):
        return self.lines[0]

    @property
    def right(self):
        return self.lines[-1]

    @staticmethod
    def in_one_box(l1, l2):
        return l1.one_line(l2)

    def left_add_line(self, line):
        assert line.start < self.left.start
        self.lines.insert(0, line)
        self.flush()

    def merge_lines(self, lines):
        i = len(lines) - 1
        while i >= 0:
            merged = False
            line = lines[i]

            # 只要跟当前箱体内的任意一条线符合箱体条件，就进入箱体
            for j in self.lines:
                if self.in_one_box(j, line):
                    self.left_add_line(line)
                    merged = True
                    break
            if not merged:
                break
            i -= 1
        return lines[:i]



class CommonGroup001(BaseStyle):
    """
    已经人工过滤了小趋势，所以趋势合并的条件应该严格：
    前提：趋势永远保持上下交替，不会出现相同类型的趋势两个趋势相邻
    合并的前提是：当前趋势融合进上一个趋势的条件是，当前趋势后续没有同级别趋势
    """
    def __init__(self, **kwargs):
        super(CommonGroup001, self).__init__(**kwargs)
        self.start = pd._libs.tslib.Timestamp(kwargs['start'])
        self.end = pd._libs.tslib.Timestamp(kwargs['end'])
        self.low_points_range = [[pd._libs.tslib.Timestamp(i[0]), pd._libs.tslib.Timestamp(i[1])] for i in
                                 kwargs['low_points_range']]
        self.high_points_range = [[pd._libs.tslib.Timestamp(i[0]), pd._libs.tslib.Timestamp(i[1])] for i in
                                  kwargs['high_points_range']]
        self.styles = None

    def set_data(self, stock_data, style_data, result_data):
        low_points = []
        for low_range in self.low_points_range:
            low_point_date = self.get_min_index(stock_data['low'], low_range)
            if low_point_date is None:
                continue
            low_points.append(Point(low_point_date, stock_data.loc[low_point_date]['high'], self.LOW, low_range))

        high_points = []
        for high_range in self.high_points_range:
            high_point_date = self.get_max_index(stock_data["high"], high_range)
            if high_point_date is None:
                continue
            high_points.append(Point(high_point_date, stock_data.loc[high_point_date]['high'], self.HIGH, high_range))

        points = low_points + high_points
        points.sort(key=lambda x: x.date)

        # 合并点
        i = 0
        length = (len(points) - 1)
        while i < length:
            point = points[i]
            next_point = points[i + 1]
            if point.type * next_point.type < 0:
                i += 1
                continue
            if point.type == self.HIGH:
                if next_point.price > point.price:
                    points[i] = next_point
            else:
                if next_point.price < point.price:
                    points[i] = next_point
            # 删除已合并的值，且不向后推进，继续合并
            points.pop(i + 1)
            length = (len(points) - 1)

        # 生成线
        i = 0
        lines = []
        while i < (len(points) - 1):
            line = Line(points[i], points[i + 1], points[i + 1].type)
            lines.append(line)
            i += 1

        # 合并线
        self.styles = []
        i = len(lines) - 1
        while i > 1:
            line = lines[i]
            pre_line = lines[i-1]

            if Box.in_one_box(pre_line, line):
                box = Box(pre_line, line)
                lines = box.merge_lines(lines[:i-1])
                self.styles.insert(0, box)
            else:
                lines = line.merge_lines(lines[:i])
                self.styles.insert(0, line)
            i = len(lines) - 1

        result_data['group_str'] = self.group_str()

    def group_str(self):
        return '|'.join([i.group_str() for i in self.styles])
