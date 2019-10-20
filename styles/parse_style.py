# coding:utf-8

import traceback

from collections import Iterable
from mindform.basestyle import Style, BaseField
from mindform.style import StyleField


class BaseParseStyle(Style):
    def __init__(self):
        self.stocks_data = {} # 存储所有个股的字段数据
        self.stocks_date = {} # 存储每只个股已计算的日期
        self.stocks_pre_data = {} # 存储每只个股前一天的数据，有计算函数自己计算，框架负责存储，并对其进行复权处理

        self.pre_data = {} # 计算单个个股时存储个股前一天的字段数据
        self.now_data = {} # 计算单个个股时存储个股当天的字段数据

        # 由计算框架注入
        self.now_k_data = None
        self.pre_k_data = None

        self.now_stock = None
        self.date = None

    def check_result(self, stock):
        for name in self.__fields__:
            if name not in self.now_data:
                raise Exception('计算个股{}数据时，字段{}未计算'.format(stock, name))

    def handle_rights(self, stock, all_history_data):
        """
        获取到个股的形态数据，根据字段配置，如果需要除权则调用对应函数除权
        :param stock:
        :param all_history_data:
        :return:
        """
        if stock not in self.stocks_data:
            return
        stock_data = self.stocks_data[stock]
        if not isinstance(stock_data, dict):
            raise Exception("ParseStyle中个股数据必须存储为dict，当前为:{}".format(type(stock_data)))
        for name in self.__fields__:
            style_field = self.__fields__[name]
            field_data = stock_data.get(name)
            style_field.handle_rights(self, field_data, all_history_data)

    def handle_data(self, stock, time, k_data):
        self.now_stock = stock
        stock_date = self.stocks_date.get(stock, None)
        if stock_date is not None:
            if time <= stock_date:
                raise Exception('个股：{} 在日期：{}的数据重复计算'.format(stock, time))
        self.date = time
        self.now_data = self.stocks_data.get(stock, None)
        self.pre_data = self.stocks_pre_data.get(stock, {})
        if self.now_data is None:
            self.now_data = self.init_first_day_data(stock, time, k_data)

        else:
            for name in self.__fields__:
                log.info("{} parse {} {}".format(self.now_stock, self.__name__, name))
                getattr(self, 'parse_' + name)()
            log_str = 'result is '
            for name in self.__fields__:
                log_str += "{}: {}, ".format(name, self.__fields__[name].format_str(self.now_data[name]))
            log.info(log_str)
        self.set_pre_data()
        self.stocks_pre_data[stock] = self.pre_data
        self.check_result(stock)
        self.stocks_data[stock] = self.now_data

    def set_pre_data(self):
        """
        由子类继承，在计算完成后调用，用于存储下一天需要用到的数据
        :return:
        """
        pass

    def set_now_stock(self, stock):
        """
        将相关数据设置为对应个股的数据
        :param stock:
        :return:
        """
        self.now_stock = stock
        self.now_data = self.stocks_data[self.now_stock]
        self.pre_data = self.stocks_pre_data[self.now_stock]

    def init_first_day_data(self, stock, time, k_data):
        return self.init_first_row(k_data)

    def __getattribute__(self, item):
        if item in super(BaseParseStyle, self).__getattribute__('__fields__'):
            return super(BaseParseStyle, self).__getattribute__('now_data')[item]

        if item.startswith('pre_'):
            if item[4:] in super(BaseParseStyle, self).__getattribute__('__fields__'):
                return super(BaseParseStyle, self).__getattribute__('pre_data').get(item)

        return super(BaseParseStyle, self).__getattribute__(item)

    def __setattr__(self, item, value):
        if item in self.__fields__:
            self.now_data[item] = value

        if item.startswith('pre_'):
            if item[5:] in self.__fields__:
                self.pre_data[item] = value

        return super(BaseParseStyle, self).__setattr__(item, value)

    def __set_styles__(self, styles):
        super(BaseParseStyle, self).__set_styles__(styles)
        BaseField.__set_styles__(styles)


class PointField(BaseField):
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


class DataField(BaseField):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        if isinstance(self.data, Iterable):
            return ",".join([str(i) for i in self.data])
        return "{}".format(self.data)


class PharseParseStyle(BaseParseStyle):
    pharse = StyleField(DataField)

    def set_pre_data(self):
        self.pre_data["pre_pharse"] = self.now_data['pharse'].data