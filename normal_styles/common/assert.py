# -*- coding: utf-8 -*- 
# @Time : 2020/1/16 0016 上午 12:42 
# @Author : Maton Zhang 
# @Site :  
# @File : assert.py 
import re

class CommonExpressionAssert():
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.start = None
        self.end = None
        self.step = None
        self.expressions = kwargs['expressions'].strip().split(';')

    def set_data(self, stock_data, style_data, result_data):
        for expression in self.expressions:
            values = re.split(r'[\+\-\*/]', expression.strip())
            for v in values:
                if v.startswith('')

