# 双均线策略
# 策略逻辑：当五日均线与二十日均线金叉时买入，当五日均线与二十日均线死叉时卖出。

# 初始化账户
import re
from collections import OrderedDict
import pandas as pd


class MindformError(Exception):
    pass

class Field(object):
    pass

class BaseStyle(object):
    def __getattr__(self, item):
        if item in self.__depends__:
            return self.__td_depends__[item]
        if item in self.__fields__:
            return self.__td_fields__[item]
        if item.startswith('pre_'):
            item = item[4:]
            if item in self.__depends__:
                return self.__yt_depends__[item]
            if item in self.__fields__:
                return self.__yt_fields__[item]

    def __setattr__(self, key, value):
        if key in self.__depends__:
            self.__td_depends__[key] = value
        if key in self.__fields__:
            self.__td_fields__[key] = value
        if key.startswith('pre_'):
            key = key[4:]
            if key in self.__depends__:
                self.__yt_depends__[key] = value
            if key in self.__fields__:
                self.__yt_fields__[key] = value



class Point(Field):
    '''
    当比较大小时，直接使用后复权数据即可
    当计算涨幅时，需要判断复权因子是否易发生改变，是则需要重新查询前复
    权数据
    '''

    def __init__(self, style, price):
        self.price = price  # 除权价格
        self.date = style.td  # 日期
        self.factor = style.td_k_data["factor"]

        self._pre_price = price  # 前复权价格
        self._pre_price_day = self.date  # 上一次前复权日期
        self._pre_factor = style.td_k_data["factor"]

    @property
    def pre_price(self):
        if self.style.td_k_data["factor"] != self._pre_factor:
            dt = get_price([style.symbol], start_date=self.date, end_date=style.td, fre_step='1d', fields=["close"],
                           skip_paused=True, fq='pre')
            self._pre_price = dt[style.symbol].iloc[0]["close"]
            self._pre_price_day = end_date = style.td

        return self._pre_price

    @property
    def pre_price_day(self):
        p = self.pre_price
        return self._pre_price_day


class StyleCreator(type):
    def __new__(cls, name, bases, attrs):
        # if name == "Style":
        #     return super(StyleCreator, cls).__new__(name, bases, attrs)
        fields = {}
        depends = {}
        for k, v in attrs.items():
            if isinstance(v, Field):
                fields[k] = v
            elif isinstance(v, BaseStyle):
                depends[k] = v
        for k in fields:
            assert ("parse_" + k) in attrs
        for k in fields:
            attrs.pop(k)
        for k in depends:
            attrs.pop(k)
        attrs['__fields__'] = fields
        attrs['__depends__'] = depends
        attrs['__name__'] = name
        return super(StyleCreator, cls).__new__(name, bases, attrs)



class Style(BaseStyle, metaclass=StyleCreator):
    depends = []  # 依赖形态，默认为空
    symbol = None  # 当前正在计算的个股的代码

    def __init__(self):
        # 设置形态拥有的字段
        assert hasattr(self, "fields")

        # 根据上市首日的数据进行初始化
        assert hasattr(self, "init_first_row")

        for field in self.fields:
            # 每个字段有对应的计算函数
            assert hasattr(self, "parse_" + field)

        self.yt = None  # 前一天的日期，由Styles设置
        self.td = None  # 当天的日期

        self.yt_k_data = None
        self.td_k_data = None

        self.yt_data = None
        self.td_data = None

        self._points = set()  # 保存所有点

    def parse(self):
        """
        整体计算函数，在所有字段计算完成后调用
        """
        pass

    def pre_parse(self, last_data, today_data, last_stock_data, today_stock_data, depend_data, yt_depend_data):
        '''
        在用户计算函数调用前执行，设置环境参数
        '''
        self.yt_data = last_data
        self.td_data = today_data

        self.yt_k_data = last_stock_data
        self.td_k_data = today_stock_data

        self.td_depend_data = depend_data
        self.yt_depend_data = yt_depend_data

    def MA(self, count):
        """
        计算均线数据
        """
        return history(self.symbol, ['open', 'close'], count, '1d', True, 'pre')['close'].mean()

    def create_point(self, price):
        """
        创建一个“点”，时间为计算当天
        price: 不复权价格，计算当天的价格肯定是不复权的价格
        """
        point = Point(self, self.td_k_data[price])
        return point

    def up_break_mas(self, mas):
        """
        收盘价在均线上方
        :param mas:
        :return:
        """
        assert isinstance(mas, list)
        for ma in mas:
            if not ma in self.mas:
                raise Exception("只能使用预先定义的均线{},当前均线{}".format(self.mas, ma))
            if not self.td_k_data["close"] > self.ma(ma):
                return False
        return True

    def accelerate_green_fall(self):
        """
        是否阴线加速下跌：前一天是阴线，当前也是阴线，收盘小于前一天，body部分大于前一天
        :return:
        """
        if self.td_k_data['close'] < self.td_k_data['open']:
            if self.td_k_data['body'] > self.yt_k_data['body']:
                return True
        return False


class Styles(object):
    """
    向styles注册形态计算类
    注册时提供：计算类

    初始化时传入关注个股列表或返回列表的函数
    s = Styles(lambda _: list(get_all_securities('stock', date)['symbol'])))

    """

    def __init__(self, get_all_stocks, engin_stock='000001.SH', mas=[10, 20, 50, 200]):
        # 保存注册的形态
        self._styles = OrderedDict()
        # 保存形态当天的计算结果，df保存，每只个股一行
        self._styles_data = {}
        # 保存形态前一天的计算结果，df保存，每只个股一行
        self._tmp_data = {}

        self.engin_stock = engin_stock
        self._get_all_stocks = get_all_stocks
        self.yt = None  # 前一天的日期，由Styles设置
        self.td = None  # 当天的日期

        self._stocks_data = {}  # 保存所有个股最近200 mas中最大的数据
        self._mas = {}  # 保存所有个股当天的均线

    def get_all_stocks(self):
        try:
            return self._get_all_stocks()
        except TypeError:
            return self._get_all_stocks

    def regist(self, style):
        name = style.name
        assert not name in self._styles
        assert isinstance(style, Style)

        # 如果之前有形态依赖该形态，则之前的形态是不可能注册成功的
        # 所以不会有循环依赖
        for i in style.depends:
            assert i in self._styles

        self._styles[name] = style
        self._styles_data[name] = pd.DataFrame(columns=style.fields)

    def run(self):
        """
        计算函数，循环计算所有已经注册了的形态
        """
        # 获取并设置当天日期
        # all_stocks = set(list(get_all_securities('stock', date)['symbol'])))

        all_stocks = set(self.get_all_stocks())

        dt = history(self.engin_stock, ['close'], 2, '1d', False, 'pre')

        self.yt = dt.index[0]
        self.td = dt.index[1]
        log.info("开始计算形态数据")
        log.info(all_stocks)

        for name in self._styles:
            style = self._styles[name]

            # 将前一天数据放入_tmp_data中，并重置_styles_data
            self._tmp_data[name] = self._styles_data[name]
            self._styles_data[name] = pd.DataFrame(columns=style.fields)

            # 如果个股当天停盘，则沿用前一天的状态
            for stock in self._tmp_data[name].index:
                if not stock in all_stocks:
                    self._styles_data[name].loc[stock, :] = self._tmp_data[name].loc[stock, :]

            # 计算形态数据
            self._run_style(style, all_stocks)

    def _init_style_data(self, style, stock):
        """
        初始化形态第一天的数据
        """
        log.info("初始化{} {}的数据".format(style.name, stock))
        first_day_stock_data = history(stock, ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor',
                                               'avg_price', 'prev_close', 'volume', 'turnover', 'quote_rate',
                                               'turnover_rate', 'amp_rate', 'is_paused', 'is_st'], 1, '1d', True,
                                       'pre').iloc[0].to_dict()
        first_day_data = style.init_first_row(first_day_stock_data)
        for field in style.fields:
            assert field in first_day_data
        log.info("初始化{} {}的结果:\n{}".format(style.name, stock, first_day_data))
        return first_day_data

    def _caculate_style_data(self, style, stock):
        """
        计算形态数据
        """
        log.info("计算{} {}的数据".format(style.name, stock))
        dt = history(stock,
                     ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor', 'avg_price', 'prev_close',
                      'volume', 'turnover', 'quote_rate', 'turnover_rate', 'amp_rate', 'is_paused', 'is_st'], 2, '1d',
                     True, 'pre').to_dict('index')
        last_stock_data = dt[self.yt]
        today_stock_data = dt[self.td]

        depend_data = {}
        yt_depend_data = {}
        for i in style.depends:
            depend_data[i.name] = style._styles_data[i.name].loc[stock, :].to_dict()
            yt_depend_data[i.name] = style._tmp_data[i.name].loc[stock, :].to_dict()

        last_data = self._tmp_data[style.name].loc[stock, :]
        today_data = {}

        style.symbol = stock

        # 在计算前调用
        style.pre_parse(last_data, today_data, last_stock_data, today_stock_data, depend_data, yt_depend_data)

        for field in style.fields:
            getattr(style, 'parse_' + field)()
            assert field in today_data

        style.parse()
        log.info("计算{} {}的数据的结果:\n{}".format(style.name, stock, str(today_data)))

        return today_data

    def _run_style(self, style, all_stocks):
        """
        真正的计算函数，计算指定的形态的数据
        """
        name = style.name

        style.yt = self.yt
        style.td = self.td

        style_data = self._tmp_data[name]
        for stock in all_stocks:
            # 如果不存在前一天的数据，说明需要初始化数据
            if not stock in style_data.index:
                today_data = self._init_style_data(style, stock)
            else:
                today_data = self._caculate_style_data(style, stock)

            self._styles_data[name].loc[stock, :] = today_data

# 加一个字段，记录进入CROSS_MA10后的最高点 以及 最高收盘价的位置
# 所有的点基本条件都是 突破所有均线
class QLPoints(Style):
    DOWN_MA10 = -1
    CROSS_MA10 = 0
    UP_MA10 = 1

    pharse = {
        CROSS_MA10: '与10日线重合',
        UP_MA10: '向上脱离10日线',
        DOWN_MA10: '向下脱离10日线'
    }

    name = "强力形态关键点"
    fields = ["pharse",
              "start",
              "force_flag", # 不为空则表示应以froce_start为起点
              "force_start", ]

    def init_first_row(self, first_day_stock_data):
        d = {}
        d["pharse"] = self.CROSS_MA10
        d["start"] = self.create_point("close")
        d["force_flag"] = None
        d["force_start"] = None

        return d

    def parse_pharse(self):
        ma = self.MA(10)
        if self.td_k_data["low"] > ma:
            self.td_data["pharse"] = self.UP_MA10
        elif self.td_k_data["high"] < ma:
            self.td_data["pharse"] = self.DOWN_MA10
        else:
            self.td_data["pharse"] = self.CROSS_MA10

    def parse_start(self):
        td_pharse = self.td_data["pharse"]
        yt_pharse = self.yt_data["pharse"]

        if td_pharse == self.DOWN_MA10 and yt_pharse > self.DOWN_MA10:
            self.td_data["start"] = self.td_k_data["open"]
        else:
            if self.td_k_data["open"] < self.td_data["start"]:
                self.td_data["start"] = self.create_point("open")

    def parse_force_flag(self):
        td_pharse = self.td_data["pharse"]
        yt_pharse = self.yt_data["pharse"]

        # 回落到10日线时产生绝对走势标志
        if td_pharse == self.CROSS_MA10 and yt_pharse == self.UP_MA10:
            self.td_data["force_flag"] = self.create_point("open")
        # 运行到10日线下方，绝对走势标志失效
        elif td_pharse < self.CROSS_MA10:
            self.td_data["force_flag"] = None

    def parse_force_start(self):
        td_pharse = self.td_data["pharse"]
        yt_pharse = self.yt_data["pharse"]

        # 在10日线上，则不影响绝对起点
        if td_pharse > self.CROSS_MA10:
            return
        # 收阴线，则无条件绝对起点结束
        elif not self.td_k_data["close"] > self.td_k_data["open"]:
            self.td_data["force_start"] = None
        # 如果之前没有绝对起点，则收阳线后即为绝对起点
        elif self.td_data["force_start"] is None:
            self.td_data["force_start"] = self.create_point("close")
        # 如果之前有绝对起点，则如果不符合条件则新的一天为绝对起点
        elif not (self.td_k_data["close"] > self.yt_k_data["close"] and self.td_k_data["high"] > self.yt_k_data[
            "high"] and self.td_k_data["open"] > self.yt_k_data["open"]):
            self.td_data["force_start"] = self.create_point("close")
        # 之前有绝对起点，当天收阳，且符合条件
        else:
            pass


class QiangLi(Style):
    BEFORE_FORMATION = -1 # 形成前
    FORMING = 0 # 形成、满足条件后创新高都是
    GOING_DOWN = 1 # 下跌中，创新高则变回FORMING
    GREEN_ARRIVE = 10 # 阴到位，正常发展最终会发展为阳到位
    DOWN_GREEN_GAP = 99 # 收阳前，向下阴跳空
    ACCELERATED_GREEN_FALL = 99 # 收阳前加速下跌
    TURN_RED = 19  # 收阳
    RED_ARRIVE = 20 # 阳到位
    TURN_GREEN = 99 # 收阳后，上涨成功前收阴
    COMPLETED = 99 # 上涨成功，结束

    depends = [QLPoints]
    fields = ["pharse",
              "XingCheng",
              "ZuiGao",
              "DaoWei",
              "2Yin"]

    def init_first_row(self, first_day_stock_data):
        d = {}
        d["pharse"] = self.BEFORE_FORMATION
        d["XingCheng"] = None
        d["ZuiGao"] = None
        d["DaoWei"] = None
        d["2Yin"] = None
        return d

    def parse_pharse(self):
        yt_pharse = self.yt_data["pharse"]
        ql = QLPoints.name

        if yt_pharse == self.BEFORE_FORMATION:
            if self.td_depend_data[ql]["pharse"] == QLPoints.UP_MA10:
                if self.up_break_mas([10, 20, 50, 200]):
                    if self.td_k_data["close"] / self.td_depend_data[ql]["start"].pre_price >= 1.18:
                        self.td_data["pharse"] = self.FORMING

        elif yt_pharse == self.FORMING:
            if self.td_depend_data[ql]["pharse"] < QLPoints.UP_MA10:
                if self.td_k_data['close'] < self.td_k_data['open']:
                    self.td_data["pharse"] = self.GREEN_ARRIVE
                else:
                    self.td_data["pharse"] = self.RED_ARRIVE
            else:
                if se

        elif yt_pharse == 1:
            # 向下跳空则结束
            if self.td_k_data['high'] < self.yt_k_data['low']:
                self.td_data["pharse"] = 10

            # 阴线向下加速
            elif self.accelerate_green_fall():
                self.td_data["pharse"] = self.ACCELERATED_GREEN_FALL

            # 收阳
            elif self.td_k_data['close'] > self.td_k_data['open']:
                self.td_data["pharse"] = 2

        elif yt_pharse == 10 or yt_pharse == 2:
            pass


# ---------------------------------------------------------------
def initialize(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '600519.SH'
    account.styles = Styles(['600519.SH'])
    account.styles.regist(TestStyle())


def get_start_date(symbol):
    """
    获取个股上市日期, 如果超过初始化函数中的回测起点则返回回测起点
    """
    start_date = get_security_info(symbol).start_date
    if start_date < account.start_date:
        return account.start_date
    else:
        return start_date


def before_trading_start(account, data):
    account.styles.run()
    pass


def after_trading_end(account, data):
    hist1 = get_candle_stick('000001.SZ', end_date='20180711', fre_step='1d', fields=['close', 'factor'],
                             skip_paused=False, fq='pre', bar_count=3)
    hist2 = get_candle_stick('000001.SZ', end_date='20180712', fre_step='1d', fields=['close', 'factor'],
                             skip_paused=False, fq='pre', bar_count=3)
    log.info(hist1)
    log.info(hist2)


# 设置买卖条件，每个交易频率（日/分钟/tick）调用一次
def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass

