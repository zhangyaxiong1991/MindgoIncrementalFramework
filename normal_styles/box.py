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

            if style_data.iloc[i][Trend.column_name] == Trend.上涨 and now_status != Box.上涨:
                up_start = self._get_up_start(stock_data, style_data, i)
                if now_status == Box.下跌:
                    self._set_down_trend(style_data, down_start, up_start)

                now_status = Box.上涨

            if style_data.iloc[i][Trend.column_name] == Trend.下跌 and now_status != Box.下跌:
                down_start = self._get_down_start(stock_data, style_data, i)
                if now_status == Box.上涨:
                    self._set_up_trend(style_data, up_start, down_start)

                now_status = Box.下跌


class MergedBox():
    column_name = 'merged_box'
    down_merge = 'merged_box_down_merge'
    up_merge = 'merged_box_up_merge'

    def _merge_down_trends_once(self, stock_data, style_data):
        now_down_trend = None
        times = 0

        for i in range(len(style_data.index)):
            down_trend = style_data.iloc[i][MergedBox.down_merge]
            if now_down_trend is None:
                now_down_trend = down_trend
            else:
                # 结尾不想等表示遇到了新的趋势
                if now_down_trend[1] < down_trend[1]:
                    back_range = (stock_data.iloc[down_trend[0]]['high'] - stock_data.iloc[now_down_trend[1]]['low']) / (stock_data.iloc[now_down_trend[0]]['high'] - stock_data.iloc[now_down_trend[1]]['low'])
                    out_range = (stock_data.iloc[now_down_trend[1]]['low'] - stock_data.iloc[down_trend[1]]['low']) / (stock_data.iloc[now_down_trend[0]]['high'] - stock_data.iloc[now_down_trend[1]]['low'])
                    if out_range > back_range:
                        now_down_trend[1] = down_trend[1]
                        times += 1
                    else:
                        now_down_trend = down_trend

            style_data[MergedBox.down_merge] = now_down_trend
        return times


    def _merge_up_trends_once(self, stock_data, style_data):
        now_up_trend = None
        times = 0

        for i in range(len(style_data.index)):
            up_trend = style_data.iloc[i][MergedBox.up_merge]
            if now_up_trend is None:
                now_up_trend = up_trend
            else:
                # 结尾不想等表示遇到了新的趋势
                if now_up_trend[1] < up_trend[1]:
                    back_range = (stock_data.iloc[now_up_trend[1]]['high'] - stock_data.iloc[up_trend[0]]['low']) / (stock_data.iloc[now_up_trend[1]]['high'] - stock_data.iloc[now_up_trend[0]]['low'])
                    out_range = (stock_data.iloc[up_trend[1]]['high'] - stock_data.iloc[now_up_trend[1]]['high']) / (stock_data.iloc[now_up_trend[1]]['high'] - stock_data.iloc[now_up_trend[0]]['low'])
                    if out_range > back_range:
                        now_up_trend[1] = up_trend[1]
                        times += 1
                    else:
                        now_up_trend = up_trend

            style_data[MergedBox.up_merge] = now_up_trend
        return times

    def _merge_down_trends(self, stock_data, style_data):
        """
        重复合并，直到不再发生合并
        :param stock_data:
        :param style_data:
        :return:
        """
        style_data[MergedBox.down_merge] = style_data[Box.down_trend]
        while True:
            times = self._merge_down_trends_once(stock_data, style_data)
            log.info(times)
            if times == 0:
                break

    def _merge_up_trends(self, stock_data, style_data):
        style_data[MergedBox.up_merge] = style_data[Box.up_trend]
        while True:
            times = self._merge_up_trends_once(stock_data, style_data)
            log.info(times)
            if times == 0:
                break

    def set_data(self, stock_data, style_data):
        self._merge_down_trends(stock_data, style_data)
        self._merge_up_trends(stock_data, style_data)
