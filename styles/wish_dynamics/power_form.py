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

    pharse = StyleField(int)
    dynamic_force_start = StyleField(PointField)
    force_start = StyleField(PointField)
    start = StyleField(PointField)

    def init_first_row(self, first_row_data, first_day_stock_data):
        first_row_data.pharse = self.CROSS_MA10
        first_row_data.start = PointField(first_day_stock_data.open)

        first_row_data.dynamic_force_start = None
        first_row_data.force_start = None
        if first_day_stock_data.close > first_day_stock_data.open:
            first_row_data.dynamic_force_start = PointField(first_day_stock_data.open)
            first_row_data.force_start = PointField(first_day_stock_data.open)

    def parse_pharse(self):
        ma = self.MA(10)
        if self.now_k_data.low > ma:
            self.now_data.pharse = self.UP_MA10
        elif self.now_k_data.high < ma:
            self.now_data.pharse = self.DOWN_MA10
        else:
            self.now_data.pharse = self.CROSS_MA10

    def parse_dynamic_force_start(self):
        # 收阴线，则无条件绝对起点结束
        if self.now_k_data.close < self.now_k_data.open:
            self.now_data.dynamic_force_start = None
        else:
            if self.now_data.dynamic_force_start is None:
                self.now_data.dynamic_force_start = PointField(self.now_k_data.open)

            # 收阳但未绝对向上，则充值动态绝对起点
            elif not (self.now_k_data.close > self.pre_k_data.close and self.now_k_data.high > self.pre_k_data.high \
                      and self.now_k_data.open > self.pre_k_data.open):
                self.now_data.dynamic_force_start = PointField(self.now_k_data.open)

    def parse_force_start(self):
        if self.now_data.pharse < self.UP_MA10 and self.pre_data.pharse == self.UP_MA10:
            self.now_data.force_start = self.now_data.dynamic_force_start

    def parse_start(self):
        if self.now_data.pharse < self.UP_MA10 and self.pre_data.pharse == self.UP_MA10:
            if self.now_data.force_start is None:
                self.now_data.start = PointField(self.now_k_data.open)
            else:
                self.now_data.start = self.now_data.force_start
        else:
            if self.now_k_data.open < self.now_data.start.price:
                self.now_data.start = PointField(self.now_k_data.open)

    def set_pre_data(self):
        super(QLPoints, self).set_pre_data()
        log.info("pharse:{}, start:{}, force_start:{}".format(self.now_data.pharse,
                                                              self.now_data.start, self.now_data['force_start']))


class QiangLi(BaseParseStyle, MAMixin):
    """
    强力形态拆成两部分，因为第一部分结束后就可以重新循环
    """
    p_形成前 = 10 # 形成前
    p_回调中 = 30 # 下跌中，创新高则变回FORMING
    p_阴到位 = 40 # 阴到位，正常发展最终会发展为阳到位
    p_收阳前 = 41
    p_阳到位 = 50
    p_收阳 = 60
    p_阴2 = 70

    p_到位阶段 = [p_阴到位, p_阳到位]

    p_到位 = 80
    p_到位后 = 81

    # 计算前会有计算框架注入对应的实例
    ql = QLPoints()

    pharse = StyleField(DataField)
    xing_cheng = StyleField(PointField)
    zui_gao = StyleField(PointField)
    dao_wei = StyleField(PointField)

    def init_first_row(self, first_row_data, first_day_stock_data):
        first_row_data.pharse = self.p_形成前
        first_row_data.xing_cheng = None
        first_row_data.zui_gao = None
        first_row_data.dao_wei = None

    def parse_pharse(self):
        if self.pre_data.pharse == self.p_形成前:
            if self.ql.now_data.pharse == QLPoints.UP_MA10:
                if self.up_break_mas([10, 20, 50, 200]):
                    if self.now_k_data.close / self.ql.now_data.start.price >= 1.18:
                        self.now_data.pharse = self.p_回调中

        elif self.pre_data.pharse == self.p_回调中:
            if self.ql.now_data.pharse < QLPoints.UP_MA10:
                self.pharse.data = self.p_到位

        elif self.pre_data.pharse == self.p_到位:
            if self.ql.pharse.data == QLPoints.DOWN_MA10:
                self.pharse.data = self.p_形成前
            else:
                self.pharse.data = self.p_到位后
        elif self.pre_data.pharse == self.p_到位后:
            if self.ql.pharse.data == QLPoints.DOWN_MA10:
                self.pharse.data = self.p_形成前
        else:
            raise Exception("强力形态位置阶段：{}".format(self.pre_data.pharse))

    def parse_xing_cheng(self):
        if self.pre_data.pharse == self.p_形成前 and self.now_data.pharse == self.p_回调中:
            self.now_data.xing_cheng = PointField()

    def parse_zui_gao(self):
        #  强力点，起点发生改变后，重新开始记录最高点
        if self.now_data.pharse == self.p_回调中:
            if self.pre_data.pharse == self.p_形成前:
                date, stock_data = self.high('high', self.ql.now_data.start.date, self.now_data.xing_cheng.date)
                self.now_data.zui_gao = PointField(stock_data.high, stock_data, date)
            else:
                if self.now_k_data.high > self.now_data.zui_gao.price:
                    self.now_data.zui_gao = PointField(self.now_k_data.high)

    def parse_dao_wei(self):
        self.now_data.pharse = self.now_data.pharse

        if self.now_data.pharse in (self.p_阳到位, self.p_阴到位):
            self.now_data.dao_wei = PointField()


class QiangLi2(PharseParseStyle, MAMixin):
    ql = QLPoints()
    p_xing_cheng = QiangLi()

    p_到位前 = 0
    p_阴到位 = 40  # 阴到位，正常发展最终会发展为阳到位
    p_收阳前 = 41
    p_阳到位 = 50
    p_收阳 = 60
    p_阴2 = 70

    pharse = StyleField(DataField)
    xing_cheng = StyleField(PointField)
    zui_gao = StyleField(PointField)
    dao_wei = StyleField(PointField)

    def init_first_row(self, first_row_data, first_day_stock_data):
        first_row_data.pharse = DataField(self.p_到位前)
        first_row_data.xing_cheng = None
        first_row_data.zui_gao = None
        first_row_data.dao_wei = None

    def parse_pharse(self):
        if self.p_xing_cheng.pharse.data == QiangLi.p_到位:
            if self.now_k_data.close < self.now_k_data.open:
                self.pharse.data = self.p_阴到位
            else:
                self.pharse.data = self.p_阳到位
        elif self.pre_pharse in (self.p_阴到位, self.p_收阳前):
            if self.向下跳空() or self.阴加速():
                self.pharse.data = self.p_到位前

            elif self.now_k_data.close > self.now_k_data.open:
                self.pharse.data = self.p_收阳

            else:
                self.pharse.data = self.p_收阳前

        elif self.pre_pharse in (self.p_阳到位, self.p_收阳):
            if self.向下跳空() or self.阴加速():
                self.pharse.data = self.p_到位前

            elif self.阴线():
                if self.now_k_data.high >= self.MA(10):
                    self.pharse.data = self.p_阴2
                else:
                    self.pharse.data = self.p_到位前
            else:
                self.pharse.data = self.p_收阳

        elif self.pre_pharse == self.p_阴2:
            self.pharse.data = self.p_到位前

    def parse_xing_cheng(self):
        if self.pharse in [self.p_阳到位, self.p_阴到位]:
            self.xing_cheng = self.p_xing_cheng.xing_cheng

    def parse_zui_gao(self):
        if self.pharse in [self.p_阳到位, self.p_阴到位]:
            self.zui_gao = self.p_xing_cheng.zui_gao

    def parse_dao_wei(self):
        if self.pharse in [self.p_阳到位, self.p_阴到位]:
            self.dao_wei = self.p_xing_cheng.dao_wei
