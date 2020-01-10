# coding:utf-8

import datetime

from normal_styles.base import BaseStyle


class DLUpDownScore(BaseStyle):
    column_name = 'DLUpDownScore'
    column_names = [column_name]

    def __init__(self, up_ranges=None, down_ranges=None):
        self._up_ranges = up_ranges or []
        self._down_ranges = down_ranges or []

    def set_data(self, stock_data, style_data):
        self.add_column_data(style_data, DLUpDownScore.column_name, 0)
        up_range_num = len(self._up_ranges)
        for up_range in self._up_ranges:
            range_data = stock_data.loc[[x for x in stock_data.index if up_range[0] <= x <= up_range[1]]]
            if len(range_data.index) == 0:
                score = 0
            else:
                low = range_data['open'].min()
                high = range_data['close'].max()
                score = high / low / up_range_num
            style_data.iloc[0][DLUpDownScore.column_name] += score

        for down_range in self._down_ranges:
            range_data = stock_data.loc[[x for x in stock_data.index if down_range[0] <= x <= down_range[1]]]
            low = range_data['close'].min()
            high = range_data['open'].max()
            score = high / low
            style_data.iloc[0][DLUpDownScore.column_name] -= score
