# coding:utf-8

import logging
import datetime

import pandas as pd

log = logging.getLogger('debug')

td = datetime.datetime.today()
yt = td - datetime.timedelta(days=1)
mock_stock_data = pd.DataFrame([[1,2,3,4],[5,6,7,8]], index=[yt, td], columns=['close', 'open', 'high', 'low'])

def history(stock_list, *args):
    if isinstance(stock_list, list):
        result = {}
        for stock in stock_list:
            result[stock] = mock_stock_data
    else:
        result = mock_stock_data
    return result
