# coding:utf-8

from mindform.style_manager import Field
from mindform.style import BaseDataType
from mindform.parse_style import ParseStyle
from mindform.data_type import Point
from mindform.mindgo import plt
from styles.wish_dynamics.power_form import QiangLiXingCheng, QLPoints, QiangLiFaZhan
from mindform.mixins import MAMixin

D_POINT_LENGTH = 0.15


class DPoint(BaseDataType):
    """
    所有已形成的D类高点
    生命周期内有三个阶段：
    全部体现
    收盘价被超越，但最高点未被超越 -- 对于当前正在使用该高点的形态来说，可能仍然有用，各形态自己保存，会被D类形态随时删除
    最高点被超越 -- 不再是D类高点
    """
    全体现 = 0
    收盘价未体现 = 1
    最高点未体现 = 2

    def __init__(self, start, point, in_use):
        self.start = start
        self.point = point
        self.status = self.全体现

    def _check(self):
        assert isinstance(self.start, Point)
        assert isinstance(self.point, Point)
        assert self.point.close / self.start.open >= 1.16

    def handle_rights(self, all_history_data):
        self.start.handle_rights(all_history_data)
        self.point.handle_rights(all_history_data)


class DPoints(ParseStyle, MAMixin):
    已形成 = 3
    均线上 = 2
    均线中 = 0
    均线下 = -2

    phase = Field(int)
    start_point = Field(Point)
    now_d_point = Field(DPoint)
    all_d_points = Field(DPoint, many=True)
    is_ready = Field(bool)

    def init_first_row(self, k_data):
        self.phase = self.已形成
        self.all_d_points = []
        start = Point()
        start.open = k_data.open / (1 + D_POINT_LENGTH)
        self.now_d_point = DPoint(start, Point(), 0)
        self.start_point = start
        self.is_ready = True  # 是否已经运行到过200 50日线上

    def parse_phase(self):
        # phase 用到is ready 提前计算
        if self.now_k_data.high > self.MA(200) and self.now_k_data.high > self.MA(50) and \
                self.now_k_data.high > self.MA(10) or self.now_k_data.high > self.MA(20):
            self.is_ready = True

        # D类失效导致起点更新，会影响判断D类形成，提前计算
        if self.all_d_points:
            # 最后一个d类的收盘价是最低的，只有超过了最后一个d类，再去遍历检查
            if self.now_k_data.close >= self.all_d_points[-1].point.close:
                low_start = self.all_d_points[-1].start
                for d_point in self.all_d_points[:-1]:
                    if d_point.status < DPoint.最高点未体现:
                        if d_point.point.close > self.now_k_data.close:
                            break

                        # 以下两种情况的D类高点都已经失效，记录状态该，并比较是否需要更新当前D类高点的起点
                        if d_point.point.high <= self.now_k_data.close:
                            d_point.status = DPoint.最高点未体现
                        else:
                            d_point.status = DPoint.收盘价未体现
                        if d_point.start.open < low_start.open:
                            low_start = d_point.start

                # 如果start是None说明已经形成D类，下次到达50 200 日线下时形成新的起点
                if self.start_point is not None:
                    if low_start.open < self.start_point.open:
                        self.start_point = low_start

        if self.pre_phase == self.已形成:
            if self.now_k_data.high < self.MA(200) or self.now_k_data.high < self.MA(50):
                self.phase = self.均线下

                self.all_d_points = [i for i in self.all_d_points if i.status == DPoint.全体现]
                self.all_d_points.append(self.now_d_point)
                self.start_point = Point()
                self.is_ready = False
                self.now_d_point = None

        else:
            if self.is_ready:
                if self.now_k_data.close > self.MA(200) and self.now_k_data.close > self.MA(50):
                    if self.now_k_data.close / self.start_point.open >= (1 + D_POINT_LENGTH):
                        self.phase = self.已形成

                        self.now_d_point = DPoint(self.start_point, Point(), DPoint.全体现)
                        self.start_point = None  # 形成后即可删除起点

            elif self.now_k_data.high < self.MA(200) or self.now_k_data.high < self.MA(50):
                self.phase = self.均线下

            elif self.now_k_data.high > self.MA(200) or self.now_k_data.high > self.MA(50):
                self.phase = self.均线上

            else:
                self.phase = self.均线中

    def parse_start_point(self):
        """
        如果当天重新设置了最低D类，且仍未形成（需要起点），新最低起点的起点参与竞争起点
        如果当天形成，则之前的起点就不再需要了，重置起点，向下运行
        如果创新低，且有起点则更新起点
        :return:
        """
        # 不需要再phase前处理，因为如果发生，一定不会形成，对phase无影响
        # todo: 有没有可能，比地点低，但是却在50 200 日线上？  应该几乎不会发生
        if not self.phase == self.已形成 and self.all_d_points is not None:
            if self.now_k_data.open < self.start_point.open:
                self.start_point = Point()

    def parse_now_d_point(self):
        """
        距离上次D类高点，到达过所有均线上方，且距离上次D类高点后的低点上涨超过15%，则形成新的D类高点
        D类高点形成后，如果创新高，D类高点也会持续更新
        :return:
        """
        if self.phase == self.已形成:
            if self.now_k_data.close > self.now_d_point.point.close:
                self.now_d_point.point = Point()


class DStyleXingCheng(ParseStyle, MAMixin):
    ql_points = QLPoints()
    qiang_li_xing_cheng = QiangLiXingCheng()
    d_points = DPoints()

    p_形成前 = 0
    p_已形成 = 1
    p_到位 = 2

    PHASE_CHOICE = {
        p_形成前: 'p_形成前',
        p_已形成: 'p_已形成',
        p_到位: 'p_到位'
    }

    is_ready = Field(bool)  # 形成前标记是否可形成D类，即是否在D类高点区
    phase = Field(int, choice=PHASE_CHOICE)
    d_point = Field(DPoint) # D类型对应的D类高点
    healthy = Field(bool) # 形成阶段是否健康

    def init_first_row(self, k_data):
        self.phase = self.p_形成前
        self.is_ready = False
        self.d_point = None
        self.healthy = None

    def parse_is_ready(self):
        """
        判断是否进入D类区域，有可能先进入D类区域，后达到涨幅，所以需要记录是否已准备好
        需要随时判断是否已经失效
        :return:
        """
        if self.d_points.all_d_points:
            # 超过了最低的D类高点，则重新判断is ready，没超过一定不用重新判断
            if self.now_k_data.close >= self.d_points.all_d_points[-1].point.high:
                self.d_point = None
                for i in self.d_points.all_d_points[-1::-1]:
                    if i.status == DPoint.最高点未体现:
                        continue
                    if self.now_k_data.high >= i.point.close and not self.now_k_data.close >= i.point.high:
                        self.is_ready = True
                        self.d_point = i
                if self.d_point is None:
                    self.is_ready = False
        else:
            self.is_ready = False

        # # 强力起点重置为当天后，上一次超过的D类高点失效
        # if self.is_ready:
        #     if self.ql_points.start.date == self.styles.td:
        #         self.is_ready = False

    def parse_phase(self):
        if self.qiang_li_xing_cheng.phase == self.qiang_li_xing_cheng.p_回调中:
            if self.is_ready:
                self.phase = self.p_已形成
        if self.qiang_li_xing_cheng.phase == self.qiang_li_xing_cheng.p_到位:
            if self.pre_phase == self.p_已形成:
                self.phase = self.p_到位
            else:
                self.phase = self.p_形成前


class DStyleFaZhan(ParseStyle, MAMixin):
    d_style_xing_cheng = DStyleXingCheng()
    qiang_li_fa_zhan = QiangLiFaZhan()

    SHANG_CHONG_FU_DU = 1.16

    p_形成前 = 0
    p_到位 = 10
    p_博大中 = 20
    p_博大后期 = 30
    p_博大成功 = 50
    p_上冲中 = 60
    p_上冲成功 = 70

    BO_DA_QI_DIAN_SHUA_XIN = [p_到位, p_博大中, p_博大后期]

    phase = Field(int)
    is_hou_qi = Field(bool)
    dao_wei = Field(Point)  # 到位点
    bo_da_qi_dian = Field(Point)  # 博大起点
    d_point = Field(Point)

    def init_first_row(self, k_data):
        self.phase = self.p_形成前
        self.is_hou_qi = False
        self.dao_wei = None
        self.bo_da_qi_dian = None
        self.d_point = None

    def parse_phase(self):
        if self.d_style_xing_cheng.phase == self.d_style_xing_cheng.p_到位:
            if self.phase != self.p_形成前:
                plt.log.warn("上冲结束前又发生D类到位，这种情况不应该存在")

            self.bo_da_qi_dian = Point()
            self.dao_wei = Point()
            self.phase = self.p_到位
            self.d_point = self.d_style_xing_cheng.d_point
            self.is_博大成功()
            self.is_上冲成功()

        elif self.pre_phase in (self.p_到位, self.p_博大中):
            self.phase = self.p_博大中
            if self.qiang_li_fa_zhan.bo_da_cheng_gong:
                self.phase = self.p_博大后期

            self.is_博大成功()
            self.is_上冲成功()

        elif self.pre_phase == self.p_博大后期:
            # todo 博大后期失败的条件是什么
            self.is_博大成功()
            self.is_上冲成功()

        elif self.pre_phase == self.p_博大成功:
            self.phase = self.p_上冲中
            self.is_上冲成功()

        elif self.pre_phase == self.p_上冲中:
            self.is_上冲成功()

    def parse_bo_da_qi_dian(self):
        if self.phase in self.BO_DA_QI_DIAN_SHUA_XIN:
            if self.open < self.bo_da_qi_dian.open:
                self.bo_da_qi_dian = Point()

    def parse_hou_qi(self):
        if self.pre_is_hou_qi:
            self.is_hou_qi = False

    def is_博大成功(self):
        self.is_博大失败()
        if self.phase in (self.p_到位, self.p_博大中):
            if self.close > self.d_point.point.high:
                self.phase = self.p_博大成功

    def is_上冲成功(self):
        self.is_上冲失败()
        if self.phase in (self.p_到位, self.p_博大中, self.p_博大成功, self.p_博大后期, self.p_上冲中):
            if self.close / self.bo_da_qi_dian.open() >= self.SHANG_CHONG_FU_DU:
                self.phase = self.p_上冲成功

    def is_博大失败(self):
        if self.qiang_li_fa_zhan.yin2 or self.qiang_li_fa_zhan.yin_jia_su or self.qiang_li_fa_zhan.yin_tiao_kong or self.qiang_li_fa_zhan.yang_hou_yin:
            self.phase = self.p_形成前

    def is_上冲失败(self):
        return