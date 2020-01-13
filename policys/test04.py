# -*- coding: utf-8 -*- 
# @Time : 2020/1/14 0014 上午 12:38 
# @Author : Maton Zhang 
# @Site :  
# @File : test04.py 

import datetime
import functools
import json

{import_items}


def init(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '000001.SH'
    account.date = datetime.datetime.strptime('{execute_date}', '%Y-%m-%d')
    account.stocks = list(get_all_securities('stock', '{execute_date}').index)
    account.styles = [{instance_items}]
    account.style_data = {}
    account.result_data = {}


def before_trading(account):
    pass


def after_trading(account):
    now = get_datetime()
    if not now.date() == account.date.date():
        log.info(now, now.date(), account.date.date())
        return

    for stock in account.stocks:
        stock_result_data = {}
        stock_style_data = {}

        # 用户设置的style都是独立的，所有依赖都已在形态内自行设置， 所以以形态为单位请求数据
        for style in account.styles:
            if stock_result_data.get('assert_error', ''):
                break

            stock_data = get_price([stock], style.start, style.end, style.step, ['close', 'open', 'low', 'high'])[stock]

            # 形态必须实现接口，返回包含依赖形态在内的所有形态数据列
            style_data = pd.DataFrame(index=stock_data.index, columns=style.get_all_columns())

            stock_style_data[style.name] = style_data
            style.set_data(stock_data, style_data, stock_result_data)

        account.result_data[stock] = stock_result_data
        account.style_data[stock] = stock_style_data


def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass
