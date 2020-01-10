# coding:utf-8

from normal_styles.base import BaseStyle
from normal_styles.trend import MergedTrend


class line:
    def __ini__(self, x1, y1, x2, y2):
        self.a = (y2 - y1) / (x2 - x1)
        self.k = y1 - (self.a * x1)


class BoxStyle:
    def __init__(self, stock_data, style_data, first_trend, second_trend):
        self._stock_data = stock_data
        self._style_data = style_data
        self._first_trend = first_trend
        self._second_trend = second_trend
        self._all_trends = [first_trend, second_trend]

    def get_now_bottom_line(self):
        first_low = Box.get_trend_low(self._all_trends[0])
        last_low = Box.get_trend_low(self._all_trends[-1])

        first_high = Box.get_trend_high(self._all_trends[0])
        last_high = Box.get_trend_high(self._all_trends[-1])

        return

    def add_trend(self, trend):


    def handle_trend(self, trend):
        


class Box(BaseStyle):
    """
    箱体：
    趋势小于或等于上一个趋势，且幅度相近  （50% -- 100% 之间  必须小于等于100%）
    结束时机 -- 当前趋势离开 箱体最新边界，且下一个趋势未回到当前最新边界内

    箱体原始边界：形成时趋势的起点 与 终点
    箱体最新边界：原始边界 顶 与最新边界顶连线
                  原始边界 底 与最新边界底连线
    """
    column_names = []

    UP = 1
    DOWN = -1

    def set_data(self, stock_data, style_data):
        all_trends = set()
        for i in range(len(style_data.index)):
            row = style_data.iloc[i]
            if row[MergedTrend.down_merge_start] >= 0 and row[MergedTrend.down_merge_end] >= 0:
                all_trends.add((row[MergedTrend.down_merge_start], row[MergedTrend.down_merge_end], Box.DOWN))
            if row[MergedTrend.up_merge_start] >= 0 and row[MergedTrend.up_merge_end] >= 0:
                all_trends.append((row[MergedTrend.up_merge_start], row[MergedTrend.up_merge_end], Box.UP))

        all_trends = list(all_trends)
        all_trends.sort(lambda x: x[0])

        now_box = None

        for trend in all_trends:

    @staticmethod
    def get_trend_low(trend):
        if trend[2] == Box.UP:
            return trend[0]
        return trend[1]

    @staticmethod
    def get_trend_high(trend):
        if trend[2] == Box.DOWN:
            return trend[0]
        return trend[1]


