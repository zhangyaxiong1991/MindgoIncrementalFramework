# coding:utf-8

from basestyle import Style

class KPoint(Style):
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

    def handle_rights(self, all_history_data):
        super(KPoint, self).handle_rights(all_history_data)
        self.k_data = all_history_data.loc[self.time].to_dict()


class Point(KPoint):
    def __init__(self, stock, time, index, k_data, price):
        super(Point, self).__init__(stock, time, k_data)
        self.price = price
        self.origin_price = price
        self.index = index

    def handle_rights(self, all_history_data):
        super(Point, self).handle_rights(all_history_data)
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
        super(TrendKPoint, self).__init__(stock, time, index, k_data)
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

    def __unicode__(self):
        return "{}: {}".format(self.time, self.trend)


class TrendPointPool(Style):
    """
    趋势起点、终点集
    """
    def __init__(self):
        self.pre_points = {}
        self.points = {}
        self.indexs = {}
        self.high_points = {}
        self.low_points = {}

    def handle_data(self, stock, time, k_data):
        index = self.indexs.get(stock, 0)
        pre_point = self.pre_points.get(stock)
        point = TrendKPoint(stock, time, index, k_data, pre_point)
        log.info("stock: {}  point status:{}".format(stock, point.trend))

        if point.trend == TrendKPoint.下跌:
            if self.low_points.get(stock) is None or point.k_data["low"] <= self.low_points[stock].k_data["low"]:
                log.info("低点比较: {} {}".format(point.k_data["low"], self.low_points[stock].k_data["low"] if stock in self.low_points else None))
                self.low_points[stock] = point
        elif point.trend == TrendKPoint.上涨:
            if self.high_points.get(stock) is None or point.k_data["high"] >= self.high_points[stock].k_data["high"]:
                self.high_points[stock] = point

        stock_point_list = self.points.setdefault(stock, [])
        if pre_point is not None:
            if pre_point.trend * point.trend < 0:
                if point.trend > 0:
                    log.info("stock:{} 低点: {}".format(stock, self.low_points[stock]))
                    stock_point_list.append(self.low_points[stock])
                    self.low_points[stock] = None
                elif point.trend < 0:
                    log.info("stock:{} 高点: {}".format(stock, self.high_points[stock]))
                    stock_point_list.append(self.high_points[stock])
                    self.high_points[stock] = None
                else:
                    pass

        self.pre_points[stock] = point
        index += 1
        self.indexs[stock] = index
        return point

    def handle_rights(self, stock, all_history_data):
        for point in self.points.get(stock, []):
            point.handle_rights(all_history_data)
        if self.pre_points.get(stock) is not None:
            self.pre_points[stock].handle_rights(all_history_data)
        if self.high_points.get(stock) is not None:
            self.high_points[stock].handle_rights(all_history_data)
        if self.low_points.get(stock) is not None:
            self.low_points[stock].handle_rights(all_history_data)
