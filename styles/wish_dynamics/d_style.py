# coding:utf-8

from mindform.style import StyleField
from styles.parse_style import BaseParseStyle, DataField, PointField
from styles.wish_dynamics.power_form import QiangLi
from mindform.mixins import MAMixin

D_POINT_LENGTH = 0.15


class DPoint(BaseParseStyle, MAMixin):
    已形成 = 3
    均线上 = 2
    均线中 = 0
    均线下 = -2

    low_d_point = StyleField(PointField)
    pharse = StyleField(DataField)
    start_point = StyleField(PointField)
    now_d_point = StyleField(PointField)
    all_d_points = StyleField(DataField)
    is_ready = StyleField(DataField)

    def init_first_day_data(self, stock, time, k_data):
        result = {}
        result["pharse"] = DataField(self.已形成)
        result["all_d_point"] = DataField([])
        result['now_d_point'] = (PointField(k_data['open'] / (1 + D_POINT_LENGTH)), PointField())
        result["low_d_point"] = None
        result["start_point"] = None
        result["is_ready"] = DataField(True)  # 是否已经运行到过200 50日线上

        # 该字段不需要，因为已形成结束的条件就是运行到 200 50 线下
        # result["is_down_ready"] = DataField(False) # 形成后是否运行到过200 50日线下
        return result

    def parse_low_d_point(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        if self.now_k_data['close'] > self.low_d_point[1].close:
            # 如果当天重新设置了最低D类，且仍未形成（需要起点），新最低起点的起点参与竞争起点
            if self.now_data['low_d_point'][0].open < self.now_data['start_point']:
                self.now_data['start_point'] = self.now_data['low_d_point'][0]

            self.now_data['low_d_point'] = None
            if self.self.now_k_data["all_d_point"].data:
                # 最后一个一定是最低的D类
                new_low = self.now_k_data["all_d_point"].data[-1]
                self.now_k_data["low_d_point"].data = new_low

    def parse_pharse(self):
        yt_pharse = self.pre_data["pre_pharse"]

        # pharse 用到is ready 提前计算
        if self.now_k_data['high'] > self.MA(200) or self.now_k_data['high'] > self.MA(50):
            self.now_data["is_ready"] = True

        if yt_pharse == self.已形成:
            if self.now_k_data['high'] < self.MA(200) or self.now_k_data['high'] < self.MA(50):
                self.now_data['parse'].data = self.均线下
        else:
            if self.now_k_data['is_ready'].data is True:
                if self.now_k_data['close'] > self.MA(200) and self.now_k_data['close'] > self.MA(50):
                    if self.now_k_data['close'] / self.now_data["start_point"].open >= (1 + D_POINT_LENGTH):
                        self.now_data['parse'] = self.已形成
            elif self.now_k_data['high'] < self.MA(200) or self.now_k_data['high'] < self.MA(50):
                self.now_data['parse'].data = self.均线下
            elif self.now_k_data['high'] > self.MA(200) or self.now_k_data['high'] > self.MA(50):
                self.now_data['parse'].data = self.均线上
            else:
                self.now_data['parse'].data = self.均线中

    def parse_start_point(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        # 不需要再pharse前处理，因为如果发生，一定不会形成，对pharse无影响
        # todo: 有没有可能，比地点低，但是却在50 200 日线上？  应该几乎不会发生
        if self.now_k_data['open'] < self.now_data['start_point'].open:
            self.now_data['start_point'] = PointField()

        # 如果当天形成，则之前的起点就不再需要了，重置起点，向下运行
        if td_pharse == self.已形成 and yt_pharse != self.已形成:
            self.now_data['start_point'] = PointField()

        # 如果当天重新设置了最低D类，且仍未形成（需要起点），新最低起点的起点参与竞争起点

    def parse_is_ready(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        if td_pharse == self.均线上:
            self.now_data["is_ready"] = True
        if td_pharse == self.均线下:
            self.now_data["is_ready"] = False

    def parse_now_d_point(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        if td_pharse == self.已形成:
            if self.now_data['now_d_point'] is None:
                self.self.now_data['now_d_point'] = (self.now_data['start_point'], PointField())
            elif self.now_k_data["close"] > self.now_data['now_d_point'][0].close:
                self.now_data['now_d_point'] = (self.now_data['now_d_point'][0], PointField())

    def parse_all_d_point(self):
        td_pharse = self.now_data["pharse"].data
        yt_pharse = self.pre_data["pre_pharse"]

        if yt_pharse == self.已形成 and td_pharse != self.已形成:
            if not self.now_data["low_d_point"][1].date == self.now_data["now_d_point"][1].date:
                self.now_data["all_d_point"].data.append(self.now_data['low_d_point'])