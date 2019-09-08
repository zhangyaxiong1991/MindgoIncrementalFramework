# coding:utf-8

from collections import OrderedDict

class StyleField:
    """
    配置类，配置字段属性
    """
    _index = 1

    def __init__(self, field_class, many=False):
        self.field_class = field_class
        self.many = many
        if hasattr(self.field_class, "handle_rights"):
            self.handle_rights = True
        else:
            self.handle_rights = False
        self._index = StyleField._index
        StyleField._index += 1

    def __set_styles__(self, styles):
        self.field_class.styles = styles


class BaseField:
    pass


class BaseMeta(object):
    k_data_fields = ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor', 'avg_price', 'prev_close',
                      'volume', 'turnover', 'quote_rate', 'turnover_rate', 'amp_rate', 'is_paused', 'is_st']
    level = 'd' # 形态默认运行在日线级别


class BaseStyle(object):
    def __set_styles__(self, styles):
        BaseStyle.styles = styles
        for k, v in self.__fields__.items():
            v.__set_styles__(styles)


class StyleCreator(type):
    def __new__(cls, name, bases, attrs):
        if name == "Style":
            return super(StyleCreator, cls).__new__(cls, name, bases, attrs)
        depends = {}
        fields = {}
        for k, v in attrs.items():
            if isinstance(v, BaseStyle):
                depends[k] = v
            if isinstance(v, StyleField):
                fields[k] = v
        for k in depends:
            attrs.pop(k)
        for k in fields:
            attrs.pop(k)
        sorted_fields = [(k, v) for k, v in fields.items()]
        sorted_fields = sorted(sorted_fields, key=lambda x: x[1]._index)
        fields = OrderedDict(sorted_fields)
        attrs['__depends__'] = depends
        attrs['__fields__'] = fields
        attrs['__name__'] = name

        new_meta = BaseMeta()
        if 'Meta' in attrs:
            for i in dir(attrs['Meta']):
                if not i.startswith('_'):
                    setattr(new_meta, i, getattr(attrs['Meta'], i))
            attrs.pop('Meta')
        attrs['_meta'] = new_meta

        return super(StyleCreator, cls).__new__(cls, name, bases, attrs)


class Style(BaseStyle, metaclass=StyleCreator):
    __catch_data_num__ = 200
    __catch_k_data__ = None

    def handle_data(self, stock, time, k_data):
        """
        计算个股对应形态上的数据
        :param stock:
        :param time:
        :param k_data:
        :return:
        """
        raise Exception('must be override')

    def handle_rights(self, stock, all_history_data):
        raise Exception('must be override')

    def set_now_stock(self, stock):
        """
        将形态的now_data, pre_data设置为对应个股的数据，用于设置依赖形态的数据
        :param stock:
        :return:
        """
        raise Exception('must be override')
