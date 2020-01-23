

# -*- coding: utf-8 -*- 
# @Time : 2020/1/14 0014 上午 12:38 
# @Author : Maton Zhang 
# @Site :  
# @File : test04.py 

import datetime
import functools
import json
from mindform.utils import MindFormDict

from normal_styles.common.group import CommonGroup001

def assert_result_data(result_data):
    assert_error = ''

    result_data['assert_error'] = assert_error

def grade_result_data(result_data):
    grade = 0

    result_data['grade'] = grade

def set_group_str(result_data, group_styles):
    group_str = '|'.join([result_data[i]['group_str'] for i in group_styles])
    result_data['group_str'] = group_str
    

def group_result_data(stocks_result_data):
    groups = {}
    for stock, result_data in stocks_result_data:
        stocks = groups.setdefault(result_data.get('group_str', ''), [])
        stocks.append(stock)
    return groups
        

def init(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '000001.SH'
    account.date = datetime.datetime.strptime('20200116', '%Y%m%d')
    account.stocks = list(get_all_securities('stock', '20200116').index[:10])
    account.styles = [CommonGroup001(**json.loads('{"step": "30m", "start": "201912111500", "end": "202001161500", "high_points_range": [["201912161500", "201912181400"], ["201912191400", "201912201430"]], "low_points_range": [["201912181400", "201912201130"], ["201912201130", "201912241430"], ["201912271130", "201912301130"]], "name": "group01"}'))]
    account.style_data = {}
    account.result_data = []
    account.error_data = []


def before_trading(account):
    pass


def after_trading(account):
    now = get_datetime()
    if not now.date() == account.date.date():
        log.info(now, now.date(), account.date.date())
        return

    for stock in account.stocks:
        stock_result_data = MindFormDict()
        stock_style_data = {}
        
        stock_result_data['grade'] = 0
        stock_result_data['assert_error'] = ''
        
        # 用户设置的style都是独立的，所有依赖都已在形态内自行设置， 所以以形态为单位请求数据
        for style in account.styles:
            stock_data = get_price([stock], style.start, style.end, style.step, ['close', 'open', 'low', 'high'])[stock]
            if len(stock_data.index) == 0:
                stock_result_data['assert_error'] = 'no data in {} -- {}'.format(style.start, style.end)
                break
                
            # 形态必须实现接口，返回包含依赖形态在内的所有形态数据列
            style_data = pd.DataFrame(index=stock_data.index, columns=style.get_all_columns())
            result_data = MindFormDict()
            result_data['error'] = ''
            
            stock_style_data[style.name] = style_data
            stock_result_data[style.name] = result_data
            
            style.set_data(stock_data, style_data, result_data)
            
            if result_data['error']:
                stock_result_data['assert_error'] += "style {} error: {}".format(style.name, result_data['error'])
        
        if not stock_result_data['assert_error']:
            assert_result_data(stock_result_data)
        
        if not stock_result_data['assert_error']:
            grade_result_data(stock_result_data)
            set_group_str(stock_result_data, ["group01"])
            account.result_data.append((stock, stock_result_data))
        else:
            account.error_data.append((stock, stock_result_data))
        account.style_data[stock] = stock_style_data
    account.result_data.sort(key=lambda x: x[1]['grade'])
    account.groups = group_result_data(account.result_data)
    log.info(account.groups)
    log.info(account.result_data[:10])
    log.info(account.result_data[-10:])
    log.info(account.error_data[:10])

def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass
