# coding:utf-8

from collections import OrderedDict

class BaseMeta(object):
    k_data_fields = ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor', 'avg_price', 'prev_close',
                      'volume', 'turnover', 'quote_rate', 'turnover_rate', 'amp_rate', 'is_paused', 'is_st']
    mas = [10, 20, 50, 200]


class Field(object):
    pass


class PointField(Field):
    pass


class PharseField(Field):
    pass


class DateField(Field):
    pass


class BaseStyle(object):
    def __getattr__(self, item):
        if item in self.__depends__:
            return self.__td_depends__[item]
        if item in self.__fields__:
            return self.__td_fields__[item]
        if item in self._meta.k_data_fields:
            return self.__td_k_data__[item]
        if item.startswith('pre_'):
            real_item = item[4:]
            if real_item in self.__depends__:
                return self.__yt_depends__[real_item]
            if real_item in self.__fields__:
                return self.__yt_fields__[real_item]
            if real_item in self._meta.k_data_fields:
                return self.__yt_k_data__[real_item]
        return super(BaseStyle, self).__getattr__(item)

    def __setattr__(self, key, value):
        if key in self.__depends__:
            raise KeyError('依赖形态：{}的值无法直接设置'.format(key))
        if key in self.__fields__:
            raise KeyError('字段：{}的值无法直接设置'.format(key))
        if key in self._meta.k_data_fields:
            raise KeyError('k线数据：{}的值无法直接设置'.format(key))
        if key.startswith('pre_'):
            real_key = key[4:]
            if real_key in self.__depends__:
                raise KeyError('依赖形态：{}的值无法直接设置'.format(real_key))
            if real_key in self.__fields__:
                raise KeyError('字段：{}的值无法直接设置'.format(real_key))
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
        for k in depends:
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


class 均线:
    def MA(self, num):
        if not num in self._meta.mas:
            raise KeyError('未在Meta.mas中定义该均线：{}，无法使用'.format(num))
        return self.__td_ma_data__[num]

    def pre_MA(self, num):
        if not num in self._meta.mas:
            raise KeyError('未在Meta.mas中定义该均线：{}，无法使用'.format(num))
        return self.__yt_ma_data__[num]


class K线均线关系(均线):
    def 向上脱离(self, mas):
        for i in mas:
            if self.low <= self.MA(i):
                return False
        return True

    def 向下脱离(self, mas):
        for i in mas:
            if self.high >= self.MA(i):
                return False
        return True

    def 交叉(self, mas):
        if self.向下脱离(mas) or self.向上脱离(mas):
            return True
        return False


class 绝对走势(Style, K线均线关系):
    class Meta:
        mas = [10, 20, 50, 200]

    pharse = PharseField()
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
    """
    def __init__(self):
        self._styles = None

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

class XX(Style):
    pass

class A(Style):
    x = XX()
    def parse_x(self):
        pass
    class Meta:
        k_data_fields = ['open', 'close']

class B(Style):
    a = A()
    x = XX()

    def parse_a(self):
        pass

    def parse_x(self):
        pass

a = 绝对走势()
a.__td_fields__["pharse"] = 1
a.__yt_fields__["pharse"] = 2
print(a.pharse)
print(a.pre_pharse)

s = Styles()
s.regist([B, A, XX])
print(s._styles)