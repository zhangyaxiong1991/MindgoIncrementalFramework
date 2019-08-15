# coding:utf-8
# 形态（style）：增量框架支持的最原始的计算器，自己处理复权，自己处理数据
# 分析形态（ParseStyle）：基于形态开发，提前定义出用到的字段、个字段的计算方法单独定义，对于复杂策略，计算模块划分更清晰
# 实现方式：框架提供字段，各字段已写好了处理复权的函数，并提供一些方便的方法。BaseParseStyle在处理数据时，搜索所有字段，
# 调用对应字段的计算函数，各计算函数通过存储的前一天的数据，以及当天已计算的字段的数据计算当天剩余字段的数据。
# 计算前框架负责填充前一天的数据 -- 将数据复制到对应字段，计算后存储对应数据


from basestyle import Style


class BaseField:
    @staticmethod
    def __set_styles__(styles):
        BaseField.styles = styles


class BaseParseStyle(Style):
    def __init__(self):
        self.stocks_data = {} # 存储所有个股的字段数据
        self.stocks_date = {} # 存储每只个股已计算的日期
        self.stocks_pre_data = {} # 存储每只个股前一天的数据，有计算函数自己计算，框架负责存储，并对其进行复权处理

        self.pre_data = None # 计算单个个股时存储个股前一天的字段数据
        self.now_data = None # 计算单个个股时存储个股当天的字段数据

        # 由计算框架注入
        self.now_k_data = None
        self.pre_k_data = None

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
            stock_field_data = stock_data.get(name)
            if stock_field_data is None:
                continue
            if style_field.handle_rights:
                if style_field.many:
                    for data in stock_field_data:
                        data.handle_rights(all_history_data)
                else:
                    stock_field_data.handle_rights(all_history_data)

    def handle_data(self, stock, time, k_data):
        stock_date = self.stocks_date.get(stock, None)
        if stock_date is not None:
            if time <= stock_date:
                raise Exception('个股：{} 在日期：{}的数据重复计算'.format(stock, time))
        self.now_data = self.stocks_data.get(stock, None)
        if self.now_data is None:
            self.now_data = self.init_first_day_data(stock, time, k_data)
        else:
            self.pre_data = self.stocks_pre_data.get(stock, {})
            for name in self.__fields__:
                getattr(self, 'parse_' + name)(stock, time, k_data)
        self.set_pre_data()
        self.stocks_pre_data[stock] = self.pre_data
        self.check_result(stock)

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

    @staticmethod
    def __set__styles__(styles):
        Style.__set__styles__(styles)
        BaseField.__set_styles__(styles)

class PointField(BaseField):
    """
    当比较大小时，直接使用后复权数据即可
    当计算涨幅时，需要判断复权因子是否易发生改变，是则需要重新查询前复
    权数据
    """
    today = None
    _rights_date = None

    def __init__(self, price=None, store_k_data=False):
        self.date = self.styels.td
        self.price = price
        self.pre_price = price
        self._store_k_data = store_k_data
        self.close = self.styels.td_k_data['close']
        self.pre_close = self.styels.td_k_data['close']

        if store_k_data:
            self.open = self.styels.td_k_data['open']
            self.high = self.styels.td_k_data['high']
            self.low = self.styels.td_k_data['low']

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
        if self.store_k_data is not None:
            self.open = all_history_data.loc[self.date]['open']
            self.high = all_history_data.loc[self.date]['high']
            self.low = all_history_data.loc[self.date]['low']

    def __cmp__(self, other):
        return self.price.__cmp__(other.price)


class DataField(BaseField):
    def __init__(self, data):
        self.data = data
