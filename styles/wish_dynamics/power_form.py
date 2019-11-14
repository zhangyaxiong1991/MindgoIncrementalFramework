# coding:utf-8

from mindform.parse_style import ParseStyle
from mindform.data_type import Point
from mindform.style import Field
from mindform.mixins import MAMixin


# 加一个字段，记录进入CROSS_MA10后的最高点 以及 最高收盘价的位置
# 所有的点基本条件都是 突破所有均线
class QLPoints(ParseStyle, MAMixin):
    DOWN_MA10 = -1
    CROSS_MA10 = 0
    UP_MA10 = 1

    PHASE_CHOICE = {
        CROSS_MA10: '与10日线重合',
        UP_MA10: '向上脱离10日线',
        DOWN_MA10: '向下脱离10日线'
    }

    phase = Field(int, choice=PHASE_CHOICE)
    dynamic_force_start = Field(Point)
    force_start = Field(Point)
    start = Field(Point)

    def init_first_row(self, first_day_stock_data):
        self.phase = self.CROSS_MA10
        self.start = Point(first_day_stock_data.open)

        self.dynamic_force_start = None
        self.force_start = None
        if first_day_stock_data.close > first_day_stock_data.open:
            self.dynamic_force_start = Point(first_day_stock_data.open)
            self.force_start = Point(first_day_stock_data.open)

    def parse_phase(self):
        ma = self.MA(10)
        if self.now_k_data.low > ma:
            self.phase = self.UP_MA10
        elif self.now_k_data.high < ma:
            self.phase = self.DOWN_MA10
        else:
            self.phase = self.CROSS_MA10

    def parse_dynamic_force_start(self):
        # 收阴线，则无条件绝对起点结束
        if self.now_k_data.close < self.now_k_data.open:
            self.dynamic_force_start = None
        else:
            if self.dynamic_force_start is None:
                self.dynamic_force_start = Point(self.now_k_data.open)

            # 收阳但未绝对向上，则充值动态绝对起点
            elif not (self.now_k_data.close > self.pre_k_data.close and self.now_k_data.high > self.pre_k_data.high \
                      and self.now_k_data.open > self.pre_k_data.open):
                self.dynamic_force_start = Point(self.now_k_data.open)

    def parse_force_start(self):
        if self.phase < self.UP_MA10 and self.pre_phase == self.UP_MA10:
            self.force_start = self.dynamic_force_start

    def parse_start(self):
        if self.phase < self.UP_MA10 and self.pre_phase == self.UP_MA10:
            if self.force_start is None:
                self.start = Point(self.now_k_data.open)
            else:
                self.start = self.force_start
        else:
            if self.now_k_data.open < self.start.price:
                self.start = Point(self.now_k_data.open)

    def set_pre_data(self):
        super(QLPoints, self).set_pre_data()
        log.info("phase:{}, start:{}, force_start:{}".format(self.phase,
                                                              self.start, self.now_data['force_start']))


class QiangLiXingCheng(ParseStyle, MAMixin):
    """
    强力形态拆成两部分，因为第一部分结束后就可以重新循环，QiangLiXingCheng 为第一阶段，从开始到回调到位
    """
    p_形成前 = 10 # 形成前
    p_回调中 = 30 # 下跌中，创新高则变回FORMING
    p_到位 = 80
    p_到位后 = 81

    PHASE_CHOICE = {
        p_形成前: 'p_形成前',
        p_形成前: 'p_形成前',
        p_回调中: 'p_回调中',
        p_到位: 'p_到位',
        p_到位后: 'p_到位后',
    }

    # 计算前会有计算框架注入对应的实例
    qiang_li_gao_dian = QLPoints()

    phase = Field(int, choice=PHASE_CHOICE)
    xing_cheng = Field(Point)
    zui_gao = Field(Point)

    def init_first_row(self, first_day_stock_data):
        self.phase = self.p_形成前
        self.xing_cheng = None
        self.zui_gao = None

    def parse_phase(self):
        if self.pre_phase == self.p_形成前:
            if self.qiang_li_gao_dian.phase == QLPoints.UP_MA10:
                if self.up_break_mas([10, 20, 50, 200]):
                    if self.now_k_data.close / self.qiang_li_gao_dian.start.price >= 1.18:
                        self.phase = self.p_回调中

        elif self.pre_phase == self.p_回调中:
            if self.qiang_li_gao_dian.phase < QLPoints.UP_MA10:
                self.phase = self.p_到位

        elif self.pre_phase == self.p_到位:
            if self.qiang_li_gao_dian.phase == QLPoints.DOWN_MA10:
                self.phase = self.p_形成前
            else:
                self.phase = self.p_到位后
        elif self.pre_phase == self.p_到位后:
            if self.qiang_li_gao_dian.phase == QLPoints.DOWN_MA10:
                self.phase = self.p_形成前
        else:
            raise Exception("强力形态位置阶段：{}".format(self.pre_phase))

    def parse_xing_cheng(self):
        if self.pre_phase == self.p_形成前 and self.phase == self.p_回调中:
            self.xing_cheng = Point()

    def parse_zui_gao(self):
        #  强力点，起点发生改变后，重新开始记录最高点
        if self.phase == self.p_回调中:
            if self.pre_phase == self.p_形成前:
                date, stock_data = self.high('high', self.qiang_li_gao_dian.start.date, self.xing_cheng.date)
                self.zui_gao = Point(stock_data.high, stock_data, date)
            else:
                if self.now_k_data.high > self.zui_gao.price:
                    self.zui_gao = Point(self.now_k_data.high)


class QiangLiFaZhan(ParseStyle, MAMixin):
    """
    强力形态拆成两部分，因为第一部分结束后就可以重新循环，QiangLiFaZhan 为第二阶段，从到位至结束
    """
    qiang_li_gao_dian = QLPoints()
    xing_cheng_jie_duan = QiangLiXingCheng()

    p_到位前 = 0
    p_阴到位 = 40  # 阴到位，正常发展最终会发展为阳到位
    p_收阳前 = 41
    p_阳到位 = 50
    p_收阳 = 60
    p_阴2 = 70

    PHASE_CHOICE = {
        p_到位前: 'p_到位前',
        p_阴到位: 'p_阴到位',
        p_收阳前: 'p_收阳前',
        p_阳到位: 'p_阳到位',
        p_收阳: 'p_收阳',
        p_阴2: 'p_阴2',
    }

    phase = Field(int, choice=PHASE_CHOICE)
    xing_cheng = Field(Point)
    zui_gao = Field(Point)
    dao_wei = Field(Point)

    def init_first_row(self, first_day_stock_data):
        self.phase = self.p_到位前
        self.xing_cheng = None
        self.zui_gao = None
        self.dao_wei = None

    def parse_phase(self):
        if self.xing_cheng_jie_duan.phase == QiangLiXingCheng.p_到位:
            if self.now_k_data.close < self.now_k_data.open:
                self.phase = self.p_阴到位
            else:
                self.phase = self.p_阳到位

        elif self.pre_phase in (self.p_阴到位, self.p_收阳前):
            if self.向下跳空() or self.阴加速():
                self.phase = self.p_到位前

            elif self.now_k_data.close > self.now_k_data.open:
                self.phase = self.p_收阳

            else:
                self.phase = self.p_收阳前

        elif self.pre_phase in (self.p_阳到位, self.p_收阳):
            if self.向下跳空() or self.阴加速():
                self.phase = self.p_到位前

            elif self.阴线():
                if self.now_k_data.high >= self.MA(10):
                    self.phase = self.p_阴2
                else:
                    self.phase = self.p_到位前
            else:
                self.phase = self.p_收阳

        elif self.pre_phase == self.p_阴2:
            self.phase = self.p_到位前

    def parse_xing_cheng(self):
        if self.phase in [self.p_阳到位, self.p_阴到位]:
            self.xing_cheng = self.xing_cheng_jie_duan.xing_cheng

    def parse_zui_gao(self):
        if self.phase in [self.p_阳到位, self.p_阴到位]:
            self.zui_gao = self.xing_cheng_jie_duan.zui_gao

    def parse_dao_wei(self):
        if self.phase in [self.p_阳到位, self.p_阴到位]:
            self.dao_wei = Point()
