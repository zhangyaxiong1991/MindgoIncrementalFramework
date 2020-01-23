# coding:utf-8
from collections import OrderedDict


class MindFormDict(OrderedDict):
    def __getattribute__(self, item):
        if item in self:
            return self[item]
        try:
            result = super(MindFormDict, self).__getattribute__(item)
        except Exception as e:
            return None
        return result

    def __setattr__(self, key, value):
        self[key] = value
