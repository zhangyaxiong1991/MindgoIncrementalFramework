# coding:utf-8

from collections import OrderedDict


class BaseDataType:
    def handle_rights(self, all_history_data):
        """
        处理复权
        :param all_history_data:
        :return:
        """


class Field:
    """
    配置类，不处理数据
    """
    _index = 1
    def __init__(self, field_class, many=False, handle_rights_items=None):
        self.field_class = field_class
        self.many = many
        self.handle_rights_items = handle_rights_items
        self._index = Field._index
        Field._index += 1

    def base_field_format_str(self, field_data):
        result = ""
        if self.handle_rights_items is not None:
            for item in self.handle_rights_items(field_data):
                result += str(item)
                result += ','
        else:
            result = str(field_data)
        return result

    def format_field_data_str(self, field_data):
        check = isinstance
        if isinstance(self.field_class, type):
            check = issubclass
        if check(self.field_class, BaseDataType):
            return self.base_field_format_str(field_data)
        elif check(self.field_class, Field):
            return self.field_class.format_str(field_data)
        else:
            raise Exception('field must be BaseDataType or Field but not {}'.format(type(self.field_class)))

    def format_str(self, field_data):
        if field_data is None:
            return 'None'
        result = ''
        if self.many:
            if isinstance(field_data, dict):
                result += '{'
                for k, item in field_data:
                    result += (str(k) + ": ")
                    result += self.format_field_data_str(item)
                    result += ","
                result += '}'
            elif isinstance(field_data, (list, set)):
                result += '['
                for item in field_data:
                    result += self.format_field_data_str(item)
                    result += ","
                result += ']'
            else:
                raise Exception("if many is True data must be dict、list or set but not {}".format(type(field_data)))
        else:
            result = self.format_field_data_str(field_data)
        return result

    def __set_styles__(self, styles):
        self.field_class.styles = styles


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
            if isinstance(v, Field):
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
