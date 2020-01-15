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
        self.start = pd._libs.tslib.Timestamp(args['start'])
        self.end = pd._libs.tslib.Timestamp(args['end'])
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
        low_date = stock_data['low'].argmin()
        high_date = stock_data['high'].argmax()
        low = stock_data['low'][low_date]
        high = stock_data['high'][high_date]
        if self.direction.upper == 'UP':
            if low >= high:
                result_data['error'] = 'not up'
                return

        if self.direction.upper == 'DOWN':
            result_data['error'] = 'not down'
            if low <= high:
                return

        if self.length:
            if not (high - low) / low >= self.length:
                result_data['error'] = 'too short: {}'.format((high - low) / low)
                return

        result_data['high'] = high
        result_data['low'] = low
        result_data['high_date'] = high_date
        result_data['low_date'] = low_date
