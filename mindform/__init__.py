# coding:utf-8

from collections import OrderedDict, Sequence

import pandas as pd

from mindgo import log, history

class BaseMeta(object):
    k_data_fields = ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor', 'avg_price', 'prev_close',
                      'volume', 'turnover', 'quote_rate', 'turnover_rate', 'amp_rate', 'is_paused', 'is_st']
    level = 'd' # 形态默认运行在日线级别


class Field(object):
    def clone(self):
        clone = self.__class__()
        return clone

    def _to_json(self):
        pass

    def _from_json(self, s):
        pass

    def _refresh_data(self, all_history_data):
        pass


class PointField(Field):
    pass


class PharseField(Field):
    def __init__(self, pharse, first_pharse=None):
        self.pharses = pharse
        self.p = first_pharse

    def clone(self):
        clone = self.__class__(self.pharses, self.p)
        return clone

class DateField(Field):
    pass


class BaseStyle(object):
    def get_depend_style_data(self, style):
        return self.styles.get_stock_style_data(self.stock, style)

    def __getattr__(self, item):
        if item in self.__depends__:
            return self.get_depend_style_data(self.__depends__[item])
        if item in self.__fields__:
            return self.__td_fields__[item]
        if item in self._meta.k_data_fields:
            return self.__td_k_data__[item]
        if item.startswith('pre_'):
            real_item = item[4:]
            if real_item in self.__fields__:
                return self.__yt_fields__[real_item]
            if real_item in self._meta.k_data_fields:
                return self.__yt_k_data__[real_item]
        return super(BaseStyle, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if key in self.__depends__:
            raise KeyError('依赖形态：{}的值无法直接设置'.format(key))
        if key in self._meta.k_data_fields:
            raise KeyError('k线数据：{}的值无法直接设置'.format(key))
        if key.startswith('pre_'):
            real_key = key[4:]
            if real_key in self.__depends__:
                raise KeyError('依赖形态：{}的值无法直接设置'.format(real_key))
            if real_key in self._meta.k_data_fields:
                raise KeyError('k线数据：{}的值无法直接设置'.format(real_key))
        return super(BaseStyle, self).__setattr__(key, value)


class StyleCreator(type):
    def __new__(cls, name, bases, attrs):
        if name == "Style":
            return super(StyleCreator, cls).__new__(cls, name, bases, attrs)
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
        attrs['__td_depends__'] = {}
        attrs['__td_fields__'] = {}
        attrs['__yt_depends__'] = {}
        attrs['__yt_fields__'] = {}
        attrs['__name__'] = name
        attrs['__td_k_data__'] = {}
        attrs['__yt_k_data__'] = {}
        new_meta = BaseMeta()
        if 'Meta' in attrs:
            for i in dir(attrs['Meta']):
                if not i.startswith('_'):
                    setattr(new_meta, i, getattr(attrs['Meta'], i))
            attrs.pop('Meta')
        attrs['_meta'] = new_meta
        return super(StyleCreator, cls).__new__(cls, name, bases, attrs)


class Style(BaseStyle, metaclass=StyleCreator):
    """
    提供K线数据查询能力
    提供个股基本K线形态查询能力  通过MIXIN类添加
    提供依赖形态查询能力
    提供增量形态计算框架：pharse： 作为一个field字段，由用户自己定义
                         用户可定义：field子类字段、style子类字段，前者为当前形态的特征字段，后者为依赖形态
                         用户可定义：对应的字段的计算函数 parse_字段名
                         用户可定义形态运行的级别：分钟、日线，默认日线 在meta中定义
                         每个周期框架首先调用依赖形态的计算函数，分别设置style的 __td_depends__、__td_fields__、
                         __yt_depends__、__yt_fields__ 为对应实例
                         框架每个周期会请求对应k线数据，分别设置style的__td_k_data__、__yt_k_data__ 为对应数据

                         用户在形态自身的计算函数中可通过self.xx self.pre_xx 引用当天与前一天的数据
    所有框架设计的字段用户均无法使用：__fields__、__depends__、__td_k_data__
    """
    __catch_data_num__ = 2
    __catch_data__ = None

    stock = None
    styles = None

    def run(self):
        for field in self.__fields__:
            log.info("计算{}形态{}字段".format(self.__name__, field))
            getattr(self, 'parse_' + field)()

        if hasattr(self, 'parse'):
            log.info("计算{}形态整体计算函数".format(self.__name__))
            self.parse()

    def clone(self):
        clone = self.__class__()
        clone.stock = self.stock
        clone.styles = self.styles
        clone.__catch_data_num__ = self.__catch_data_num__
        clone.__catch_data__ = self.__catch_data__

        clone.__fields__ = clone.__fields__
        clone.__depends__ = clone.__depends__
        clone.__td_fields__ = {}
        clone.__yt_fields__ = {}
        clone.__td_k_data__ = {}
        clone.__yt_k_data__ = {}
        return clone

    def set_td_k_data(self, stock_k_data):
        """
        设置当天股票数据
        :param stock_k_data:
        :return:
        """
        self.__yt_k_data__ = self.__td_k_data__
        self.__td_k_data__ = dict(stock_k_data)

    def set_styles(self, styles):
        self.styles = styles

    def set_stock(self, stock):
        self.stock = stock

    def init_fields(self):
        self.__td_fields__ = {}
        for name, field in self.__fields__.items():
            self.__td_fields__[name] = field.clone()

    def switch_fields(self):
        """
        将td field至为yt field，且如果用户不显示修改td，则td持续不变
        :return:
        """
        self.__yt_fields__ = {}
        for name, field in self.__td_fields__.items():
            self.__yt_fields__[name] = field.clone()

    def pre_init_first_row(self):
        self.init_fields()


class MA(Style):
    MAX_MA_NUM = 200
    __ma_nums__ = set()

    def __new__(cls, nums, *args, **kwargs):
        nums = [int(i) for i in nums]
        for i in nums:
            assert 0 < i < cls.MAX_MA_NUM
            cls.__ma_nums__.add(i)
        cls.__catch_data_num__ = max(cls.__ma_nums__)

    @classmethod
    def now(cls, target, num):
        assert num in cls.__ma_nums__
        return cls.__catch_data__.iloc[-num:][target].sum() / num

    @classmethod
    def pre(cls, target, num):
        assert num in cls.__ma_nums__
        return cls.__catch_data__.iloc[-(num+1):-1][target].sum() / num


class K线均线关系(Style):
    ma = MA([10])  # 这里定义计算单元

    def __init__(self, nums):
        nums = [int(i) for i in nums]
        nums = sorted(list(set(nums)))
        self._nums = nums
        self.ma = MA(nums)   # 向MA计算单元注册均线
        self.__name__ = self.__name__ + '_' + '_'.join(map(lambda x: str(x), nums)) # 根据传入的参数成为唯一的计算单元

    def 向上脱离(self):
        for i in self._nums:
            if self.low <= self.ma.now(i):
                return False
        return True

    def 向下脱离(self):
        for i in self._nums:
            if self.high >= self.ma.now(i):
                return False
        return True

    def 交叉(self, mas):
        if self.向下脱离(mas) or self.向上脱离(mas):
            return True
        return False

    def pre_向上脱离(self):
        for i in self._nums:
            if self.pre_low <= self.ma.pre(i):
                return False
        return True

    def pre_向下脱离(self):
        for i in self._nums:
            if self.pre_high >= self.ma.pre(i):
                return False
        return True

    def pre_交叉(self):
        if self.pre_向下脱离 or self.pre_向上脱离:
            return True
        return False

# 当形态拥有字段时，说明是用户形态，不应再用框架的技巧，这里需要显示定义用到的均线
# 如果要做成一个灵活的可佩的形态，则该形态应该属于框架形态，字段应该换成函数
# 总结：用户形态 用字段，框架形态用函数
class 绝对走势(Style):
    均线关系 = K线均线关系([10])
    # pharse = PharseField()
    start = PointField()
    force_flag = DateField()
    force_start = DateField()

    def parse_pharse(self):
        pass

    def parse_start(self):
        pass

    def parse_force_flag(self):
        pass

    def parse_force_start(self):
        pass


class Styles(object):
    """
    统筹管理所有形态的类，用户定义的形态类必须注册进Styles中，Styles负责驱动各形态，在各个股票上各个周期的计算
    用户在整体分析函数中可通过Styles实例引用他注册的Style在个股上的数据
    注册style直接定义即可
    style会在所有的关注个股上计算，Styles只会在驱动个股上计算，Styles会实时更新最新的关注个股

    通过依赖关系决定计算顺序
    遍历未分配列表，对没有依赖或所有依赖都已被分配的添加至已分配列表，并从未分配列表中删除。如果未分配列表空则结束，如果一次循环
    没有找到任何可分配对象则判定为存在循环依赖

    增量计算的最大特点：当发生除权时，所有记录的点、历史数据等都需要更新

    推进时的计算顺序：逐个股票、逐个形态计算,计算前设置形态symble，K线数据、依赖形态数据（形态内的字段计算由形态自己控制）
    """
    def __init__(self, driver, follow_stocks):
        self._driver = driver  # 驱动个股

        # 关注的股票
        self._follow_stocks = follow_stocks

        # 注册的形态
        self._styles = None

        # 用户形态数据  {"个股代码": {"形态名": {"字段名": 字段值}}}
        self._style_data = {}
        self._pre_style_data = {}

        # 缓存的所有个股的数据
        self._catch_data = {}

    def regist(self, styles):
        if not self._styles is None:
            raise Exception('只能注册一次形态')
        self._styles = OrderedDict()
        styles = list(set(styles))
        assert len(styles) > 0
        styles = [i if isinstance(i, Style) else i() for i in styles]
        for i in styles:
            assert isinstance(i, Style)
        styles = set(styles)
        while 1:
            if len(styles) == 0:
                break
            hit_style = []
            not_registed_style = []
            not_hited_style = []
            for style in styles:
                style_not_registed_style = []
                style_not_hited_style = []
                for _, depend_style in style.__depends__.items():
                    if depend_style.__name__ in self._styles:  # 已分配
                        continue
                    elif depend_style not in styles: # 未注册
                        style_not_registed_style.append(depend_style)
                    else: # 已注册，但仍未分配，可能该形态太存在依赖
                        style_not_hited_style.append(depend_style)

                not_registed_style += style_not_registed_style
                not_hited_style += style_not_hited_style

                if not (style_not_registed_style or style_not_hited_style):
                    hit_style.append(style)

            if not hit_style and not not_registed_style:
                raise Exception('存在循环依赖{}'.format(styles))
            if hit_style:
                for i in hit_style:
                    styles.remove(i)
                    self._styles[i.__name__] = i
            if not_registed_style:
                for i in not_registed_style:
                    styles.add(i)
        self.__catch_data_num__ = 2
        for style_name, style in self._styles.items():
            if style.__catch_data_num__ > self.__catch_data_num__:
                self.__catch_data_num__ = style.__catch_data_num__

    def _handle_rights(self, symble, now):
        """
        当个股数据是发生除权时，请求历史数据，更新该个股对应各字段的值
        :param symble:
        :param now:
        :return:
        """
        all_history_data = self._get_all_history_data(symble, now)
        catch_k_data = self._catch_data[symble]
        new_catch_k_data = all_history_data.loc[catch_k_data.index, :]
        self._catch_data[symble] = new_catch_k_data

        symble_data = self._style_data[symble]
        for style_name, style in self._styles.items():
            # 刷新各字段的数据
            style_data = symble_data[style_name]
            for field_name, field_json_data in style_data.items():
                field = style.__fields__[field_name]
                field.from_json(field_json_data)
                field._handle_rights(all_history_data)
                style_data[field_name] = field.to_json

    def _refresh_symble_data(self, symble, last_two_days_data, now):
        """
        更新个股相关数据，增量更新
        :param symble:
        :param now:
        :return:
        """
        catched_k_data = self._catch_data[symble]
        if not last_two_days_data.iloc[0]['close'] == catched_k_data.iloc[-1]['close']:
            self._handle_rights(symble, now)
            catched_k_data = self._catch_data[symble] # 除权后数据已更新，需要重新获取
        if len(catched_k_data) >= self.__catch_data_num__:
            catched_k_data.drop(catched_k_data.index[0:1], inplace=True)
            catched_k_data = catched_k_data.append(last_two_days_data.iloc[1])

    def get_all_stocks(self):
        """
        获取所有关注的个股
        :return:
        """
        try:
            return self._follow_stocks()
        except TypeError:
            return self._follow_stocks

    def get_stock_style_data(self, stock, style):
        """
        获取指定个股，指定形态的数据
        :param stock:
        :param style:
        :return:
        """
        if isinstance(style, str):
            key = style + '_' + stock
        else:
            key = style.__name__ + '_' + stock
        return self._style_data.get(key, None)

    def set_stock_style_data(self, stock, style, data):
        if isinstance(style, str):
            key = style + '_' + stock
        else:
            key = style.__name__ + '_' + stock
        self._style_data[key] = data

    def _run_style(self):
        """
        收盘逐个个股、按照依赖关系逐个计算形态计算数据
        :return:
        """
        all_stocks = self.get_all_stocks()

        dt = history(self._driver, ['close'], 2, '1d', False, 'pre')
        all_stocks_data = history(all_stocks, ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor',
                                               'avg_price', 'prev_close', 'volume', 'turnover', 'quote_rate',
                                               'turnover_rate', 'amp_rate', 'is_paused', 'is_st'], 2, '1d', False, 'pre')

        self.yt = dt.index[0]
        self.td = dt.index[1]
        log.info("开始计算{}形态数据".format(self.td))
        log.info(all_stocks)

        for name in self._styles:
            for stock in all_stocks:
                stock_td_k_data = all_stocks_data.get(stock, None)
                if stock_td_k_data is None:   # 还未上市
                    continue
                stock_td = stock_td_k_data.index[-1]
                stock_yt = stock_td_k_data.index[0]
                stock_style_data = self.get_stock_style_data(stock, name)

                # 个股当天停盘
                if not stock_td == self.td:
                    continue

                # 之前没有数据，代表是上市第一天
                if stock_style_data is None:
                    stock_style_data = self._styles[name].clone()
                    stock_style_data.set_stock(stock)
                    stock_style_data.set_styles(self)
                    stock_style_data.set_td_k_data(stock_td_k_data)
                    stock_style_data.pre_init_first_row()
                    stock_style_data.init_first_row()                   # 用户开发
                    self.set_stock_style_data(stock, name, stock_style_data)

                else:
                    stock_style_data.set_td_k_data(stock_td_k_data)
                    stock_style_data.switch_fields()
                    stock_style_data.run()

    def before_trading_start(self, account, data):
        """
        在开盘前调用，请求所有的个股的状态，判断是否需要除权，
        如果需要：则请求该个股的所有历史数据，遍历该个股下的所有形态的所有字段，更新值
        todo： 如果在开盘时无法立即判断除权，则在收盘后计算前判断
        :return:
        """
        pass

    def handle_data(self, account, data):
        """
        每个交易频率（日/分钟/tick）调用一次, 请求所有关注个股的tick、分钟数据，驱动需要在该级别运行形态
        :return:
        """
        pass

    def after_trading_end(self, account, data):
        """
        收盘后请求所有关注个股的日线数据，驱动需要在该级别运行的形态
        之后转换数据，将当天数据置为前一天数据，为下一天计算做准备
        :return:
        """
        self._run_style()
        pass


class XX(Style):
    PHARSE_1 = 1
    pharse_chocie = {
        PHARSE_1: "阶段1",
    }
    pharse = PharseField(pharse_chocie, PHARSE_1)
    def parse_pharse(self):
        self.pharse.p += 1
    def init_first_row(self):
        self.pharse.p = 1

class A(Style):
    x = XX()
    def init_first_row(self):
        print(self.x)
        pass
    class Meta:
        k_data_fields = ['open', 'close']

class B(Style):
    a = A()
    x = XX()
    def init_first_row(self):
        pass

    def parse(self):
        print(self.a.x.pharse.p)
        print(self.x.pharse.p)

s = Styles('000001', ['600086'])
s.regist([B, A, XX])
while True:
    s.after_trading_end(1, 1)

a = 绝对走势()
a.__td_fields__["pharse"] = 1
a.__yt_fields__["pharse"] = 2
print(a.pharse)
print(a.pre_pharse)