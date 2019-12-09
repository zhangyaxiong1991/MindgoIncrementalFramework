# coding:utf-8
from collections import OrderedDict


class MindFormDict(OrderedDict):
    def __getattribute__(self, item):
        if item in self:
            return self[item]
        result = super(MindFormDict, self).__getattribute__(item)
        if result is None:
            raise Exception('value error')
        return result

    def __setattr__(self, key, value):
        self[key] = value
