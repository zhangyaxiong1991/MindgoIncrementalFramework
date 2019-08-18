# coding:utf-8

import datetime

from mindform.style import Styles
from styles.point_style import TrendPointPool


def init(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '600519.SH'
    s = Styles('000001.SH', ['600086.SH'], datetime.datetime.strptime('20190501', "%Y%m%d"))
    s.regist([TrendPointPool])


def before_trading(account):
    pass


def after_trading(account):
    log.info("after_trading_end:{}".format(get_datetime()))
    account.styles.after_trading_end(account)
    log.info(account.styles._styles['TrendPointPool'].points.get('600089.SH'))


def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass