# coding:utf-8

from basestyle import Style

class KData:
    today = None
    _rights_date = None

    def _handle_rights(self, all_history_data):
        """
        处理复权
        :param all_history_data:
        :return:
        """
        self._rights_date = self.today


class KPoint(KData):
    """
    基础K线点
    """
    def __init__(self, stock, time, index, k_data):
        """
        :param stock:
        :param time:
        :param index: k线所在点的x轴坐标
        :param k_data:
        """
        self.stock = stock
        self.time = time
        self.index = index
        self.k_data = k_data
        self.origin_k_data = k_data

    def _handle_rights(self, all_history_data):
        super()._rights_date(all_history_data)
        self.k_data = all_history_data[self.time]


class Point(KPoint):
    def __init__(self, stock, time, index, k_data, price):
        super().__init__(stock, time, k_data)
        self.price = price
        self.origin_price = price
        self.index = index

    def _handle_rights(self, all_history_data):
        super()._handle_rights(all_history_data)
        self.price = self.k_data["close"] / self.origin_k_data["close"] * self.origin_price


class TrendKPoint(KPoint):
    上涨 = 3
    平上涨 = 1
    平 = 0
    平下跌 = -1
    下跌 = -3

    def __init__(self, stock, time, index, k_data, pre=None):
        """
        :param pre: 前一个点，用于对当天趋势的判断，但并不需保存
        """
        super().__init__(stock, time, index, k_data)
        if pre is None:
            self.trend = self.平

        if pre is not None:
            assert isinstance(pre, TrendKPoint)
            if pre.trend == self.上涨 or pre.trend == self.平上涨:
                if self.k_data['high'] > pre.k_data['high']:
                    self.trend = self.上涨
                elif self.k_data['low'] < pre.k_data['low']:
                    self.trend = self.下跌
                else:
                    self.trend = self.平上涨

            elif pre.trend == self.下跌 or pre.trend == self.平下跌:
                if self.k_data['low'] < pre.k_data['low']:
                    self.trend = self.下跌
                elif self.k_data['high'] > pre.k_data['high']:
                    self.trend = self.上涨
                else:
                    self.trend = self.平下跌

            else:
                if self.k_data['low'] < pre.k_data['low'] and self.k_data['high'] > pre.k_data['high']:
                    self.trend = self.平
                elif self.k_data['low'] < pre.k_data['low']:
                    self.trend = self.下跌
                elif self.k_data['high'] > pre.k_data['high']:
                    self.trend = self.上涨
                else:
                    self.trend = self.平


class TrendPointPool(Style):
    """
    趋势起点、终点集
    """
    def __init__(self):
        self.pre_points = {}
        self.points = {}
        self.indexs = {}

    def handle_data(self, stock, time, k_data):
        self.indexs.setdefault(stock, 0)
        self.indexs[stock] += 1
        point = TrendKPoint(stock, time, self.indexs[stock], k_data, self.pre_points.get(stock))
        self.pre_points[stock] = point
        stock_point_list = self.points.setdefault(stock, [])
        stock_point_list.append(point)
        return point

    def handle_rights(self, stock, all_history_data):
        for point in self.points.get(stock, []):
            point.handle_rights(all_history_data)
        if self.pre_points[stock]:
            self.pre_points[stock].handle_rights(all_history_data)
