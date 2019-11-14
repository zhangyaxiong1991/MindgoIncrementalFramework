# coding:utf-8

import traceback

from mindform.style import Style, BaseDataType
from mindform.utils import MindFormDict


class ParseStyle(Style):
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

    def handle_field_data_rights(self, field_data, all_history_data):
        """
        形态字段的复权处理函数，
        :param field_data: 存储在形态中的，当前正在处理的个股的，该字段的值
        :param all_history_data: 当前正在处理的个股的历史数据
        :return:
        """
        if isinstance(field_data, BaseDataType):
            field_data.handle_rights(all_history_data)
        elif isinstance(field_data, (list, set, tuple)):
            for i in field_data:
                self.handle_field_data_rights(i, all_history_data)
        elif isinstance(field_data, dict):
            for k, v in field_data:
                self.handle_field_data_rights(v, all_history_data)
        return

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
            field_data = stock_data.get(name)
            self.handle_field_data_rights(field_data, all_history_data)

    def check_result(self, stock):
        for name in self.__fields__:
            if name not in self.now_data:
                raise Exception('计算个股{}数据时，字段{}未计算'.format(stock, name))

    def handle_data(self, stock, time, k_data):
        k_data = MindFormDict(k_data)
        self.now_stock = stock
        stock_date = self.stocks_date.get(stock, None)
        if stock_date is not None:
            if time <= stock_date:
                raise Exception('个股：{} 在日期：{}的数据重复计算'.format(stock, time))
        self.date = time
        self.now_data = self.stocks_data.get(stock, MindFormDict())
        self.pre_data = self.stocks_pre_data.get(stock, MindFormDict())
        if not self.now_data:
            self.now_data = MindFormDict()
            self.init_first_row(k_data)

        else:
            for name in self.__fields__:
                log.info("{} parse {} {}".format(self.now_stock, self.__name__, name))
                if callable(getattr(self, 'parse_' + name)):
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
        self.pre_data = MindFormDict()
        self.pre_phase = self.phase

    def set_now_stock(self, stock):
        """
        将相关数据设置为对应个股的数据
        :param stock:
        :return:
        """
        self.now_stock = stock
        self.now_data = self.stocks_data[self.now_stock]
        self.pre_data = self.stocks_pre_data[self.now_stock]

    def __getattribute__(self, item):
        if item in super(ParseStyle, self).__getattribute__('__fields__'):
            return super(ParseStyle, self).__getattribute__('now_data')[item]

        if item.startswith('pre_'):
            if item[4:] in super(ParseStyle, self).__getattribute__('__fields__'):
                return super(ParseStyle, self).__getattribute__('pre_data').get(item)

        return super(ParseStyle, self).__getattribute__(item)

    def __setattr__(self, item, value):
        if item in self.__fields__:
            self.now_data[item] = value

        if item.startswith('pre_'):
            if item[4:] in self.__fields__:
                self.pre_data[item] = value

        return super(ParseStyle, self).__setattr__(item, value)

    def __set_styles__(self, styles):
        super(ParseStyle, self).__set_styles__(styles)
        BaseDataType.__set_styles__(styles)
