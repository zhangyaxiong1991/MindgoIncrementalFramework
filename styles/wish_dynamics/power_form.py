# coding:utf-8

import os

from mindform.basestyle import Style
from styles.parse_style import *
from mindform.basestyle import StyleField
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
        if self.now_k_data["low"] > ma:
            self.now_data["pharse"].data = self.UP_MA10
        elif self.now_k_data["high"] < ma:
            self.now_data["pharse"].data = self.DOWN_MA10
        else:
            self.now_data["pharse"].data = self.CROSS_MA10

    def parse_start(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        if td_pharse == self.DOWN_MA10 and yt_pharse > self.DOWN_MA10:
            self.now_data["start"] = PointField(self.now_k_data["open"])
        else:
            if self.now_k_data["open"] < self.now_data["start"].price:
                self.now_data["start"] = PointField(self.now_k_data["open"])

    def parse_force_flag(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        # 回落到10日线时产生绝对走势标志
        if td_pharse == self.CROSS_MA10 and yt_pharse == self.UP_MA10:
            self.now_data["force_flag"] = PointField(self.now_k_data["open"])
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
        elif not self.now_k_data["close"] > self.now_k_data["open"]:
            self.now_data["force_start"] = None
        # 如果之前没有绝对起点，则收阳线后即为绝对起点
        elif self.now_data["force_start"] is None:
            self.now_data["force_start"] = PointField(self.now_k_data["close"])
        # 如果之前有绝对起点，则如果不符合条件则新的一天为绝对起点
        elif not (self.now_k_data["close"] > self.pre_k_data["close"] and self.now_k_data["high"] > self.pre_k_data[
            "high"] and self.now_k_data["open"] > self.pre_k_data["open"]):
            self.now_data["force_start"] = PointField(self.now_k_data["close"])
        # 之前有绝对起点，当天收阳，且符合条件
        else:
            pass

    def set_pre_data(self):
        self.pre_data["pre_pharse"] = self.now_data["pharse"].data
        log.info("pharse:{}, start:{}".format(self.now_data["pharse"].data, self.now_data["start"].date))


class QiangLi(Style, MAMixin):
    p_形成前 = 10 # 形成前
    p_回调中 = 30 # 下跌中，创新高则变回FORMING
    p_阴到位 = 40 # 阴到位，正常发展最终会发展为阳到位
    p_收阳前 = 41
    p_阳到位 = 50
    p_收阳 = 60
    p_阴2 = 70

    # 计算前会有计算框架注入对应的实例
    ql = QLPoints()

    pharse = StyleField(DataField)
    xing_cheng = StyleField(PointField)
    zui_gao = StyleField(PointField)
    dao_wei = StyleField(PointField)

    def init_first_row(self, first_day_stock_data):
        d = {}
        d["pharse"] = DataField(self.p_形成前)
        d["xing_cheng"] = None
        d["zui_gao"] = None
        d["dao_wei"] = None
        return d

    def parse_pharse(self):
        yt_pharse = self.pre_data["pharse"]

        if yt_pharse == self.p_形成前:
            if self.ql.now_data["pharse"].data == QLPoints.UP_MA10:
                if self.up_break_mas([10, 20, 50, 200]):
                    if self.now_k_data["close"] / self.ql.now_data["start"].price >= 1.18:
                        self.now_data["pharse"].data = self.p_回调中

        elif yt_pharse == self.p_回调中:
            if self.ql.now_data["pharse"].data < QLPoints.UP_MA10:
                if self.now_k_data['close'] < self.now_k_data['open']:
                    self.now_data["pharse"].data = self.p_阴到位
                else:
                    self.now_data["pharse"].data = self.p_阳到位

        elif yt_pharse in (self.p_阴到位, self.p_收阳):
            if self.向下跳空() or self.阴加速():
                self.now_data["pharse"].data = self.p_形成前

            elif self.now_k_data['close'] > self.now_k_data['open']:
                self.now_data["pharse"].data = self.p_收阳

            else:
                self.now_data["pharse"].data = self.p_收阳前

        elif yt_pharse in (self.p_阳到位, self.p_收阳):
            if self.向下跳空() or self.阴加速():
                self.now_data["pharse"].data = self.p_形成前

            elif self.阴线():
                if self.now_k_data['high'] >= self.MA(10):
                    self.now_data["pharse"].data = self.p_阴2
                else:
                    self.now_data["pharse"].data = self.p_形成前

            else:
                self.now_data["pharse"].data = self.p_收阳

        elif yt_pharse == self.p_阴2:
            self.now_data["pharse"].data = self.p_形成前

        else:
            raise Exception("强力形态位置阶段：{}".format(yt_pharse))

    def parse_xing_cheng(self):
        pre_pharse = self.pre_data["pharse"]
        now_pharse = self.now_data["pharse"].data

        if pre_pharse == self.p_形成前 and now_pharse == self.p_回调中:
            self.now_data['xing_cheng'] = PointField(store_k_data=True)

    def parse_zui_gao(self):
        pre_pharse = self.pre_data["pharse"]
        now_pharse = self.now_data["pharse"].data

        if now_pharse in (self.p_形成前, self.p_回调中):
            if self.ql.now_data['start'].date 

        if self.ql.now_data['start'].date


    def set_pre_data(self):
        self.pre_data["pharse"] = self.now_data["pharse"].data



