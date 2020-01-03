# coding:utf-8

from normal_styles.base import BaseStyle


class KTrend(BaseStyle):
    column_name = 'k_trend'
    column_names = [column_name]
    
    上涨 = '3'
    平上涨 = '1'
    平 = '0'
    平下跌 = '-1'
    下跌 = '-3'
    
    def set_data(self, stock_data, style_data):
        if KTrend.column_name not in style_data.columns:
            self.add_column_data(style_data, KTrend.column_name, KTrend.平)

        for i in range(len(stock_data.index)):
            if i == 0:
                pre = None
                pre_style = None
            else:
                pre = stock_data.iloc[i - 1]
                pre_style = style_data.iloc[i - 1]
            now = stock_data.iloc[i]
            now_style = style_data.iloc[i]

            if pre is not None:
                if pre_style[KTrend.column_name] == KTrend.上涨 or pre_style[KTrend.column_name] == KTrend.平上涨:
                    if now['high'] > pre['high']:
                        now_style[KTrend.column_name] = KTrend.上涨
                    elif now['low'] < pre['low']:
                        now_style[KTrend.column_name] = KTrend.下跌
                    else:
                        now_style[KTrend.column_name] = KTrend.平上涨

                elif pre_style[KTrend.column_name] == KTrend.下跌 or pre_style[KTrend.column_name] == KTrend.平下跌:
                    if now['low'] < pre['low']:
                        now_style[KTrend.column_name] = KTrend.下跌
                    elif now['high'] > pre['high']:
                        now_style[KTrend.column_name] = KTrend.上涨
                    else:
                        now_style[KTrend.column_name] = KTrend.平下跌

                else:
                    if now['low'] < pre['low'] and now['high'] > pre['high']:
                        now_style[KTrend.column_name] = KTrend.平
                    elif now['low'] < pre['low']:
                        now_style[KTrend.column_name] = KTrend.下跌
                    elif now['high'] > pre['high']:
                        now_style[KTrend.column_name] = KTrend.上涨
                    else:
                        now_style[KTrend.column_name] = KTrend.平


class Trend(BaseStyle):
    column_name = 'trend'
    down_trend_start = 'trend_ds'
    down_trend_end = 'trend_de'
    up_trend_start = 'trend_us'
    up_trend_end = 'trend_ue'
    column_names = [column_name, down_trend_start, down_trend_end, up_trend_start, up_trend_end]

    上涨 = 1
    下跌 = -1
    平 = 0

    def _get_up_start(self, stock_data, style_data, i):
        i = i - 1
        low = 99999
        low_index = None
        while i >= 0:
            if stock_data.iloc[i]['low'] < low:
                low_index = i
            if style_data.iloc[i][KTrend.column_name] == KTrend.下跌:
                break
            i -= 1
        return low_index

    def _set_down_trend(self, style_data, down_start, up_start):
        i = down_start
        while i <= up_start:
            style_data.iloc[i][Trend.down_trend_start] = down_start
            style_data.iloc[i][Trend.down_trend_end] = up_start
            i += 1

    def _get_down_start(self, stock_data, style_data, i):
        i = i - 1
        high = -1
        high_index = None
        while i >= 0:
            if stock_data.iloc[i]['high'] > high:
                high_index = i
            if style_data.iloc[i][KTrend.column_name] == KTrend.上涨:
                break
            i -= 1
        return high_index

    def _set_up_trend(self, style_data, up_start, down_start):
        i = up_start
        while i <= down_start:
            style_data.iloc[i][Trend.up_trend_start] = up_start
            style_data.iloc[i][Trend.up_trend_end] = down_start
            i += 1

    def set_data(self, stock_data, style_data):
        self.add_column_data(style_data, Trend.up_trend_start, -1)
        self.add_column_data(style_data, Trend.up_trend_end, -1)
        self.add_column_data(style_data, Trend.down_trend_start, -1)
        self.add_column_data(style_data, Trend.down_trend_end, -1)

        now_status = None
        up_start = 0
        down_start = 0
        for i in range(len(style_data.index)):
            log.info(now_status, up_start, down_start, i)
            if i == 0:
                now_status = Trend.平
                continue

            if style_data.iloc[i][KTrend.column_name] == KTrend.上涨 and now_status != Trend.上涨:
                up_start = self._get_up_start(stock_data, style_data, i)
                if now_status == Trend.下跌:
                    self._set_down_trend(style_data, down_start, up_start)

                now_status = Trend.上涨

            if style_data.iloc[i][KTrend.column_name] == KTrend.下跌 and now_status != Trend.下跌:
                down_start = self._get_down_start(stock_data, style_data, i)
                if now_status == Trend.上涨:
                    self._set_up_trend(style_data, up_start, down_start)

                now_status = Trend.下跌

        if now_status == Trend.上涨:
            log.info("end set up:", up_start, len(style_data.index)-1)
            self._set_up_trend(style_data, up_start, len(style_data.index)-1)
        if now_status == Trend.下跌:
            log.info("end set down:", down_start, len(style_data.index) - 1)
            self._set_down_trend(style_data, down_start, len(style_data.index)-1)


class MergedTrend(BaseStyle):
    column_name = 'merged_t'
    down_merge_start = 'merged_t_ds'
    down_merge_end = 'merged_t_de'
    up_merge_start = 'merged_t_us'
    up_merge_end = 'merged_t_ue'
    column_names = [column_name, down_merge_start, down_merge_end, up_merge_start, up_merge_end]

    def _set_down_merge_trend(self, style_data, down_merge_start, down_merge_end):
        i = down_merge_start
        while i <= down_merge_end:
            style_data.iloc[i][MergedTrend.down_merge_start] = down_merge_start
            style_data.iloc[i][MergedTrend.down_merge_end] = down_merge_end
            i += 1
        log.info(style_data.iloc[down_merge_start: down_merge_end])

    def _set_up_merge_trend(self, style_data, up_merge_start, up_merge_end):
        i = up_merge_start
        while i <= up_merge_end:
            style_data.iloc[i][MergedTrend.up_merge_start] = up_merge_start
            style_data.iloc[i][MergedTrend.up_merge_end] = up_merge_end
            i += 1
        log.info(style_data.iloc[up_merge_start: up_merge_end])

    def _merge_down_trends_once(self, stock_data, style_data):
        now_down_trend = None
        times = 0

        for i in range(len(style_data.index)):
            if style_data.iloc[i][MergedTrend.down_merge_start] is None:
                continue

            down_trend = [style_data.iloc[i][MergedTrend.down_merge_start], style_data.iloc[i][MergedTrend.down_merge_end]]
            if down_trend[0] == -1:
                continue
            if now_down_trend is None:
                now_down_trend = down_trend
            else:
                # 结尾不想等表示遇到了新的趋势
                if now_down_trend[1] < down_trend[1]:
                    if self.merge_down(stock_data, now_down_trend, down_trend):
                        now_down_trend[1] = down_trend[1]
                        times += 1
                    else:
                        self._set_down_merge_trend(style_data, now_down_trend[0], now_down_trend[1])
                        now_down_trend = down_trend
        self._set_down_merge_trend(style_data, now_down_trend[0], now_down_trend[1])
        return times

    def _merge_up_trends_once(self, stock_data, style_data):
        now_up_trend = None
        times = 0

        for i in range(len(style_data.index)):
            if style_data.iloc[i][MergedTrend.up_merge_start] is None:
                continue

            up_trend = [style_data.iloc[i][MergedTrend.up_merge_start], style_data.iloc[i][MergedTrend.up_merge_end]]
            if now_up_trend is None:
                now_up_trend = up_trend
            else:
                # 结尾不想等表示遇到了新的趋势
                if now_up_trend[1] < up_trend[1]:
                    if self.merge_up(stock_data, now_up_trend, up_trend):
                        now_up_trend[1] = up_trend[1]
                        times += 1
                    else:
                        self._set_up_merge_trend(style_data, now_up_trend[0], now_up_trend[1])
                        now_up_trend = up_trend
        self._set_up_merge_trend(style_data, now_up_trend[0], now_up_trend[1])
        return times

    def _merge_down_trends(self, stock_data, style_data):
        """
        重复合并，直到不再发生合并
        :param stock_data:
        :param style_data:
        :return:
        """
        style_data[MergedTrend.down_merge_start] = style_data[Trend.down_trend_start]
        style_data[MergedTrend.down_merge_end] = style_data[Trend.down_trend_end]
        while True:
            times = self._merge_down_trends_once(stock_data, style_data)
            log.info(times)
            if times == 0:
                break

    def _merge_up_trends(self, stock_data, style_data):
        style_data[MergedTrend.up_merge_start] = style_data[Trend.up_trend_start]
        style_data[MergedTrend.up_merge_end] = style_data[Trend.up_trend_end]
        while True:
            times = self._merge_up_trends_once(stock_data, style_data)
            log.info(times)
            if times == 0:
                break

    def merge_up(self, stock_data, left_up_trend, right_up_trend):
        back_range = (stock_data.iloc[left_up_trend[1]]['high'] - stock_data.iloc[right_up_trend[0]]['low']) / (
                stock_data.iloc[left_up_trend[1]]['high'] - stock_data.iloc[left_up_trend[0]]['low'])
        out_range = (stock_data.iloc[right_up_trend[1]]['high'] - stock_data.iloc[left_up_trend[1]]['high']) / (
                stock_data.iloc[left_up_trend[1]]['high'] - stock_data.iloc[left_up_trend[0]]['low'])
        if out_range > back_range:
            log.info("merge up", left_up_trend, right_up_trend, out_range, back_range, stock_data.index[left_up_trend[0]])
            return True
        return False

    def merge_down(self, stock_data, left_down_trend, right_down_trend):
        back_range = (stock_data.iloc[right_down_trend[0]]['high'] - stock_data.iloc[left_down_trend[1]][
            'low']) / (stock_data.iloc[left_down_trend[0]]['high'] - stock_data.iloc[left_down_trend[1]][
            'low'])
        out_range = (stock_data.iloc[left_down_trend[1]]['low'] - stock_data.iloc[right_down_trend[1]]['low']) / (
                stock_data.iloc[left_down_trend[0]]['high'] - stock_data.iloc[left_down_trend[1]]['low'])
        if out_range > back_range:
            log.info("merge down", left_down_trend, right_down_trend, out_range, back_range)
            return True
        return False

    def _large_eat_small(self, stock_data, style_data):
        for i in range(len(style_data.index)):
            if style_data.iloc[i][MergedTrend.up_merge_start] < style_data.iloc[i][MergedTrend.down_merge_start] and style_data.iloc[i][MergedTrend.up_merge_end] > style_data.iloc[i][MergedTrend.down_merge_end]:
                style_data.iloc[i][MergedTrend.down_merge_start] = -1
                style_data.iloc[i][MergedTrend.down_merge_end] = -1

            if style_data.iloc[i][MergedTrend.up_merge_start] > style_data.iloc[i][MergedTrend.down_merge_start] and style_data.iloc[i][MergedTrend.up_merge_end] < style_data.iloc[i][MergedTrend.down_merge_end]:
                style_data.iloc[i][MergedTrend.up_merge_start] = -1
                style_data.iloc[i][MergedTrend.up_merge_end] = -1


    def set_data(self, stock_data, style_data):
        self.add_column_data(style_data, MergedTrend.down_merge_start, -1)
        self.add_column_data(style_data, MergedTrend.down_merge_end, -1)
        self.add_column_data(style_data, MergedTrend.up_merge_start, -1)
        self.add_column_data(style_data, MergedTrend.up_merge_end, -1)
        self._merge_down_trends(stock_data, style_data)
        self._merge_up_trends(stock_data, style_data)
        self._large_eat_small(stock_data, style_data)
