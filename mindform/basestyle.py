# coding:utf-8


class BaseMeta(object):
    k_data_fields = ['open', 'high', 'low', 'close', 'high_limit', 'low_limit', 'factor', 'avg_price', 'prev_close',
                      'volume', 'turnover', 'quote_rate', 'turnover_rate', 'amp_rate', 'is_paused', 'is_st']
    level = 'd' # 形态默认运行在日线级别


class BaseStyle(object):
    def __setattr__(self, key, value):
        if key in self.__depends__:
            raise KeyError('依赖形态：{}的值无法直接设置'.format(key))
        return super(BaseStyle, self).__setattr__(key, value)


class StyleCreator(type):
    def __new__(cls, name, bases, attrs):
        if name == "Style":
            return super(StyleCreator, cls).__new__(cls, name, bases, attrs)
        depends = {}
        for k, v in attrs.items():
            if isinstance(v, BaseStyle):
                depends[k] = v
        for k in depends:
            attrs.pop(k)
        attrs['__depends__'] = depends
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
    __catch_data_num__ = 2

    def handle_data(self, stock, time, k_data):
        pass

    def handle_rights(self, stock, all_history_data):
        pass