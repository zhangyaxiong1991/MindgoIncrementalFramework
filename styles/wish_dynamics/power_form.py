# coding:utf-8

from styles.point_style import Style
from styles.parse_style import BaseParseStyle, DataField, PointField
from basestyle import StyleField
from mindform.mixins import MAMixin


# 加一个字段，记录进入CROSS_MA10后的最高点 以及 最高收盘价的位置
# 所有的点基本条件都是 突破所有均线
class QLPoints(BaseParseStyle, MAMixin):
    DOWN_MA10 = -1
    CROSS_MA10 = 0
    UP_MA10 = 1

    pharse = {
        CROSS_MA10: '与10日线重合',
        UP_MA10: '向上脱离10日线',
        DOWN_MA10: '向下脱离10日线'
    }

    pharse = StyleField(DataField)
    start = StyleField(PointField)
    force_flag = StyleField(DataField)
    force_start = StyleField(PointField)

    def init_first_row(self, first_day_stock_data):
        d = {}
        d["pharse"] = DataField(self.CROSS_MA10)
        d["start"] = PointField(first_day_stock_data["close"])
        d["force_flag"] = None
        d["force_start"] = None
        return d

    def parse_pharse(self):
        ma = self.MA(10)
        if self.td_k_data["low"] > ma:
            self.now_data["pharse"].data = self.UP_MA10
        elif self.td_k_data["high"] < ma:
            self.now_data["pharse"].data = self.DOWN_MA10
        else:
            self.now_data["pharse"].data = self.CROSS_MA10

    def parse_start(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        if td_pharse == self.DOWN_MA10 and yt_pharse > self.DOWN_MA10:
            self.now_data["start"] = PointField(self.td_k_data["open"])
        else:
            if self.td_k_data["open"] < self.now_data["start"].price:
                self.now_data["start"] = PointField(self.td_k_data["open"])

    def parse_force_flag(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        # 回落到10日线时产生绝对走势标志
        if td_pharse == self.CROSS_MA10 and yt_pharse == self.UP_MA10:
            self.now_data["force_flag"] = PointField(self.td_k_data["open"])
        # 运行到10日线下方，绝对走势标志失效
        elif td_pharse < self.CROSS_MA10:
            self.now_data["force_flag"] = None

    def parse_force_start(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        # 在10日线上，则不影响绝对起点
        if td_pharse > self.CROSS_MA10:
            return
        # 收阴线，则无条件绝对起点结束
        elif not self.td_k_data["close"] > self.td_k_data["open"]:
            self.now_data["force_start"] = None
        # 如果之前没有绝对起点，则收阳线后即为绝对起点
        elif self.now_data["force_start"] is None:
            self.now_data["force_start"] = PointField(self.td_k_data["close"])
        # 如果之前有绝对起点，则如果不符合条件则新的一天为绝对起点
        elif not (self.td_k_data["close"] > self.yt_k_data["close"] and self.td_k_data["high"] > self.yt_k_data[
            "high"] and self.td_k_data["open"] > self.yt_k_data["open"]):
            self.now_data["force_start"] = PointField(self.td_k_data["close"])
        # 之前有绝对起点，当天收阳，且符合条件
        else:
            pass

    def set_pre_data(self):
        self.pre_data["pre_pharse"] = self.now_data["pharse"].data


class QiangLi(Style, MAMixin):
    BEFORE_FORMATION = -1 # 形成前
    FORMING = 0 # 形成、满足条件后创新高都是
    GOING_DOWN = 1 # 下跌中，创新高则变回FORMING
    GREEN_ARRIVE = 10 # 阴到位，正常发展最终会发展为阳到位
    DOWN_GREEN_GAP = 99 # 收阳前，向下阴跳空
    ACCELERATED_GREEN_FALL = 99 # 收阳前加速下跌
    TURN_RED = 19  # 收阳
    RED_ARRIVE = 20 # 阳到位
    TURN_GREEN = 99 # 收阳后，上涨成功前收阴
    COMPLETED = 99 # 上涨成功，结束

    # 计算前会有计算框架注入对应的实例
    ql = QLPoints()

    pharse = StyleField(DataField)
    XingCheng = StyleField(PointField)
    ZuiGao = StyleField(PointField)
    DaoWei = StyleField(PointField)
    DaoWei = StyleField(PointField)
    yin2 = StyleField(PointField)

    def init_first_row(self, first_day_stock_data):
        d = {}
        d["pharse"] = DataField(self.BEFORE_FORMATION)
        d["XingCheng"] = None
        d["ZuiGao"] = None
        d["DaoWei"] = None
        d["2Yin"] = None
        return d

    def parse_pharse(self):
        yt_pharse = self.pre_data["pharse"].data

        if yt_pharse == self.BEFORE_FORMATION:
            if self.ql.now_data["pharse"].data == QLPoints.UP_MA10:
                if self.up_break_mas([10, 20, 50, 200]):
                    if self.td_k_data["close"] / self.ql.now_data["start"].price >= 1.18:
                        self.now_data["pharse"] = self.FORMING

        elif yt_pharse == self.FORMING:
            if self.ql.now_data["pharse"].data < QLPoints.UP_MA10:
                if self.td_k_data['close'] < self.td_k_data['open']:
                    self.now_data["pharse"].data = self.GREEN_ARRIVE
                else:
                    self.now_data["pharse"].data = self.RED_ARRIVE
            else:
                if se

        elif yt_pharse == 1:
            # 向下跳空则结束
            if self.td_k_data['high'] < self.yt_k_data['low']:
                self.now_data["pharse"] = 10

            # 阴线向下加速
            elif self.accelerate_green_fall():
                self.now_data["pharse"] = self.ACCELERATED_GREEN_FALL

            # 收阳
            elif self.td_k_data['close'] > self.td_k_data['open']:
                self.now_data["pharse"] = 2

        elif yt_pharse == 10 or yt_pharse == 2:
            pass


# ---------------------------------------------------------------
def initialize(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '600519.SH'
    account.styles = Styles(['600519.SH'])
    account.styles.regist(TestStyle())


def get_start_date(symbol):
    """
    获取个股上市日期, 如果超过初始化函数中的回测起点则返回回测起点
    """
    start_date = get_security_info(symbol).start_date
    if start_date < account.start_date:
        return account.start_date
    else:
        return start_date


def before_trading_start(account, data):
    account.styles.run()
    pass


def after_trading_end(account, data):
    hist1 = get_candle_stick('000001.SZ', end_date='20180711', fre_step='1d', fields=['close', 'factor'],
                             skip_paused=False, fq='pre', bar_count=3)
    hist2 = get_candle_stick('000001.SZ', end_date='20180712', fre_step='1d', fields=['close', 'factor'],
                             skip_paused=False, fq='pre', bar_count=3)
    log.info(hist1)
    log.info(hist2)


# 设置买卖条件，每个交易频率（日/分钟/tick）调用一次
def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass

