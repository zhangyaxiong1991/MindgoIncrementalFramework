# coding:utf-8

from mindform.style import StyleField
from mindform.basestyle import Style, BaseField
from styles.parse_style import BaseParseStyle, DataField, PointField, PharseParseStyle
from styles.wish_dynamics.power_form import QiangLi
from mindform.mixins import MAMixin

D_POINT_LENGTH = 0.15


class DPointField(BaseField):
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
        assert isinstance(self.start, PointField)
        assert isinstance(self.d_point, PointField)
        assert self.d_point.close / self.start.open >= 1.16

    def handle_rights(self, all_history_data):
        self.start.handle_rights(all_history_data)
        self.d_point.handle_rights(all_history_data)


class DPoint(BaseParseStyle, MAMixin):
    已形成 = 3
    均线上 = 2
    均线中 = 0
    均线下 = -2

    pharse = StyleField(int)
    start_point = StyleField(PointField)
    now_d_point = StyleField(DPointField)
    all_d_points = StyleField(DPointField, many=True)
    is_ready = StyleField(bool)

    def init_first_day_data(self, first_row_data, time, k_data):
        first_row_data.pharse = self.已形成
        first_row_data.all_d_points = []
        start = PointField()
        start.open = k_data.open / (1 + D_POINT_LENGTH)
        first_row_data.now_d_point = DPointField(start, PointField(), 0)
        first_row_data.start_point = start
        first_row_data.is_ready = True  # 是否已经运行到过200 50日线上

    def parse_pharse(self):
        # pharse 用到is ready 提前计算
        if self.now_k_data.high > self.MA(200) and self.now_k_data.high > self.MA(50) and \
                self.now_k_data.high > self.MA(10) or self.now_k_data.high > self.MA(20):
            self.now_data.is_ready = True

        # D类失效导致起点更新，会影响判断D类形成，提前计算
        if self.now_data.all_d_points:
            # 最后一个d类的收盘价是最低的，只有超过了最后一个d类，再去遍历检查
            if self.now_k_data.close >= self.now_data.all_d_points[-1].point.close:
                low_start = self.now_data.all_d_points[-1].start
                for d_point in self.now_data.all_d_points[:-1]:
                    if d_point.status < DPointField.最高点未体现:
                        if d_point.point.close > self.now_k_data.close:
                            break

                        # 以下两种情况的D类高点都已经失效，记录状态该，并比较是否需要更新当前D类高点的起点
                        if d_point.point.high <= self.now_k_data.close:
                            d_point.status = DPointField.最高点未体现
                        else:
                            d_point.status = DPointField.收盘价未体现
                        if d_point.start.open < low_start.open:
                            low_start = d_point.start

                # 如果start是None说明已经形成D类，下次到达50 200 日线下时形成新的起点
                if self.now_data.start_point is not None:
                    if low_start.open < self.now_data.start_point.open:
                        self.now_data.start_point = low_start

        if self.pre_data.pharse == self.已形成:
            if self.now_k_data.high < self.MA(200) or self.now_k_data.high < self.MA(50):
                self.now_data.pharse = self.均线下

                self.now_data.all_d_points = [i for i in self.now_data.all_d_points if i.status == DPointField.全体现]
                self.now_data.all_d_points.append(self.now_data.now_d_point)
                self.now_data.start_point = PointField()
                self.now_data.is_ready = False
                self.now_data.now_d_point = None

        else:
            if self.now_data.is_ready:
                if self.now_k_data.close > self.MA(200) and self.now_k_data.close > self.MA(50):
                    if self.now_k_data.close / self.now_data.start_point.open >= (1 + D_POINT_LENGTH):
                        self.now_data.pharse = self.已形成

                        self.now_data.now_d_point = DPointField(self.now_data.start_point, PointField(), DPointField.全体现)
                        self.now_data.start_point = None  # 形成后即可删除起点

            elif self.now_k_data.high < self.MA(200) or self.now_k_data.high < self.MA(50):
                self.now_data.pharse = self.均线下

            elif self.now_k_data.high > self.MA(200) or self.now_k_data.high > self.MA(50):
                self.now_data.pharse = self.均线上

            else:
                self.now_data.pharse = self.均线中

    def parse_start_point(self):
        """
        如果当天重新设置了最低D类，且仍未形成（需要起点），新最低起点的起点参与竞争起点
        如果当天形成，则之前的起点就不再需要了，重置起点，向下运行
        如果创新低，且有起点则更新起点
        :return:
        """
        td_pharse = self.now_data.pharse

        # 不需要再pharse前处理，因为如果发生，一定不会形成，对pharse无影响
        # todo: 有没有可能，比地点低，但是却在50 200 日线上？  应该几乎不会发生
        if not td_pharse == self.已形成 and self.now_data.all_d_points is not None:
            if self.now_k_data.open < self.now_data.start_point.open:
                self.now_data.all_d_points = PointField()

    def parse_now_d_point(self):
        """
        距离上次D类高点，到达过所有均线上方，且距离上次D类高点后的低点上涨超过15%，则形成新的D类高点
        D类高点形成后，如果创新高，D类高点也会持续更新
        :return:
        """
        if self.now_data.pharse == self.已形成:
            if self.now_k_data.close > self.now_data.now_d_point.point.close:
                self.now_data.now_d_point.point = PointField()


class BaseDStyle(PharseParseStyle, MAMixin):
    ql = QiangLi()
    d_points = DPoint()

    p_形成前 = 0
    p_已形成 = 1
    p_到位 = 2

    is_ready = StyleField(DataField)  # 形成前标记是否可形成D类，即是否在D类高点区
    pharse = StyleField(DataField)
    d_point = StyleField(PointField, many=True) # D类型对应的D类高点
    healthy = StyleField(DataField) # 形成阶段是否健康

    def init_first_day_data(self, stock, time, k_data):
        result = {}
        result['pharse'] = DataField(self.p_形成前)
        result['is_ready'] = DataField(False)
        result['d_point'] = None
        result['healthy'] = None
        return result

    def parse_is_ready(self):
        """
        判断是否进入D类区域，有可能先进入D类区域，后达到涨幅，所以需要记录是否已准备好
        需要随时判断是否已经失效
        :return:
        """
        if not self.is_ready.data or self.now_k_data.close >= self.d_point[1].high:
            found = False
            for i in self.d_points.all_d_points[-1::-1]:
                if i[2].data == DPoint.最高点未体现:
                    continue
                if self.now_k_data.high >= i[1].close and not self.now_k_data.close >= i[1].high:
                    self.is_ready.data = True
                    found = True
            if not found:
                self.is_ready.data = False

    def parse_pharse(self):
        if self.ql.pharse == self.ql.p_回调中:
            if self.is_ready.data:
                self.pharse = self.p_已形成
        if self.ql.pharse in self.ql.p_到位阶段:
            if self.pre_is_ready:
                self.pharse = self.p_到位
            else:
                self.pharse = self.p_形成前


class DStyle(PharseParseStyle, MAMixin):
    xing_cheng = BaseDStyle

    p_已到位 = 2
    p_博大失败 = 2
    p_博大成功 = 5
