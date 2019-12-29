# coding:utf-8

from normal_styles.trend import Trend


class Box:
    column_name = 'k_box'
    down_trend = 'k_box_down'
    up_trend = 'k_box_up'

    上涨 = 1
    下跌 = -1
    平 = 0

    def _get_up_start(self, stock_data, style_data, i):
        i = i - 1
        low  = 99999
        low_index = None
        while i >= 0:
            if stock_data.iloc[i]['low'] < low:
                low_index = i
            if style_data.iloc[i][Trend.column_name] == Trend.下跌:
                break
        return low_index

    def _set_down_trend(self, style_data, down_start, up_start):
        i = down_start
        while i <= up_start:
            style_data.iloc[i][Box.down_trend] = (down_start, up_start)
            i += 1

    def _get_down_start(self, stock_data, style_data, i):
        i = i - 1
        high = -1
        high_index = None
        while i >= 0:
            if stock_data.iloc[i]['high'] > high:
                high_index = i
            if style_data.iloc[i][Trend.column_name] == Trend.上涨:
                break
        return high_index

    def _set_up_trend(self, style_data, up_start, down_start):
        i = up_start
        while i <= down_start:
            style_data.iloc[i][Box.up_trend] = (up_start, down_start)
            i += 1

    def set_data(self, stock_data, style_data):
        style_data[Box.up_trend] = None
        style_data[Box.down_trend] = None

        now_status = None
        up_start = None
        down_start = None
        for i in range(len(style_data.index)):
            if i == 0:
                now_status = Box.平
                continue

            if stock_data.iloc[i][Trend.column_name] == Trend.上涨 and now_status != Box.上涨:
                up_start = self._get_up_start(stock_data, style_data, i)
                if now_status == Box.下跌:
                    self._set_down_trend(style_data, down_start, up_start)

                now_status = Box.上涨

            if stock_data.iloc[i][Trend.column_name] == Trend.下跌 and now_status != Box.下跌:
                down_start = self._get_down_start(stock_data, style_data, i)
                if now_status == Box.上涨:
                    self._set_up_trend(style_data, up_start, down_start)

                now_status = Box.下跌
