# coding:utf-8

from mindform.style import BaseDataType


class Point(BaseDataType):
    """
    当比较大小时，直接使用后复权数据即可
    当计算涨幅时，需要判断复权因子是否易发生改变，是则需要重新查询前复
    权数据
    """
    today = None
    _rights_date = None

    def __init__(self, price=None, stock_k_data=None, date=None):
        self.date = date
        if self.date is None:
            self.date = self.styles.td
        self.price = price
        self.pre_price = price

        if stock_k_data is None:
            self.close = self.styles.now_k_data['close']
            self.pre_close = self.styles.now_k_data['close']
            self.open = self.styles.now_k_data['open']
            self.high = self.styles.now_k_data['high']
            self.low = self.styles.now_k_data['low']
        else:
            self.close = stock_k_data['close']
            self.pre_close = stock_k_data['close']
            self.open = stock_k_data['open']
            self.high = stock_k_data['high']
            self.low = stock_k_data['low']

    def handle_rights(self, all_history_data):
        """
        处理复权
        :param all_history_data:
        :return:
        """
        self.close = all_history_data.loc[self.date]['close']
        factor = self.close / self.pre_close
        if self.price is not None:
            self.price = self.pre_price * factor
        self.open = all_history_data.loc[self.date]['open']
        self.high = all_history_data.loc[self.date]['high']
        self.low = all_history_data.loc[self.date]['low']

    def __cmp__(self, other):
        return self.price.__cmp__(other.price)

    def __str__(self):
        return "点|{}|{}".format(self.date, self.price)
