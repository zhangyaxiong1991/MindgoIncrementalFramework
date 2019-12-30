# coding: utf-8

import datetime

from normal_styles.box import Box, MergedBox
from normal_styles.trend import Trend


def get_stock_grade(stock_data, style_data):
    log.info(style_data)


def init(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '000001.SH'
    account.date = datetime.datetime.strptime('2019-12-20', '%Y-%m-%d')
    account.stocks = ['000001.SH']
    account.styles = [Trend(), Box(), MergedBox]
    account.stock_data_range = {'1d': ('20190807', '20191223')}
    account.stock_grade = {}


def before_trading(account):
    pass


def after_trading(account):
    now = get_datetime()
    if not now.date() == account.date.date():
        log.info(now, now.date(), account.date.date())
        return

    for stock in account.stocks:
        stock_data = {}
        style_data = {}
        for step in account.stock_data_range:
            step_stock_data = get_price([stock], account.stock_data_range[step][0], account.stock_data_range[step][1], step, ['close', 'open', 'low', 'high'])[stock]
            step_style_data = pd.DataFrame([[]], index=step_stock_data.index)
            stock_data['step_' + step] = step_stock_data
            style_data['step_' + step] = step_style_data
            for style in account.styles:
                log.info('set style data: {}'.format(style.column_name))
                style.set_data(step_stock_data, step_style_data)
        account.stock_grade[stock] = get_stock_grade(stock_data, style_data)


def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass
