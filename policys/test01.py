# coding: utf-8
import datetime
from mindform.style_manager import StyleManager
from styles.wish_dynamics.power_form import QLPoints, QiangLiXingCheng, QiangLiFaZhan
from styles.wish_dynamics.d_style import DStyleXingCheng, DStyleFaZhan
from mindform.mindgo import plt


def init(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '000001.SH'
    s = StyleManager('000001.SH', ['000413.SZ'], datetime.datetime.strptime('20150527', "%Y%m%d"))
    s.regist([DStyleFaZhan])
    account.styles = s


def before_trading(account):
    pass


def after_trading(account):
    plt.log.info("after_trading_end:{}".format(plt.get_datetime()))
    account.styles.after_trading_end(account)


def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass