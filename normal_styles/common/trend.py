# -*- coding: utf-8 -*- 
# @Time : 2020/1/10 下午 8:21
# @Author : Maton Zhang 
# @Site :  
# @File : trend.py

from normal_styles.base import BaseStyle


class CommonTrend001(BaseStyle):
    def __init__(self, **args):
        # 用户传参
        self.name = args['name']
        self.step = args['step']
        self.start = args['start']
        self.end = args['end']
        self.direction = args['direction']
        self.length = args['length']

    def set_data(self, stock_data, style_data, result_data):
        """
        形态数据计算入口
        :param stock_data: 个股数据
        :param style_data: 形态数据，对个股数据的扩充，df
        :param result_data: 计算结果, 字典形式存储
        :return:
        """
        style_result_data = {}
        data = stock_data.loc[[x for x in stock_data.index if self.start <= x <= self.end]]
        low_date = data['low'].argmin()
        high_date = data['high'].argmax()
        low = data['low'][low_date]
        high = data['high'][high_date]
        if self.direction.upper == 'UP':
            if low >= high:
                return

        if self.direction.upper == 'DOWN':
            if low <= high:
                return

        if self.length:
            if not (high - low) / low >= self.length:
                return

        style_result_data['high'] = high
        style_result_data['low'] = low
        style_result_data['high_date'] = high_date
        style_result_data['low_date'] = low_date
        result_data[self.name] = style_result_data
