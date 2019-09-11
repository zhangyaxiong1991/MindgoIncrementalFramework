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

    pharse = StyleField(DataField)
    start_point = StyleField(PointField)
    now_d_point = StyleField(DataField)
    all_d_points = StyleField(DataField)
    is_ready = StyleField(DataField)

    def init_first_day_data(self, stock, time, k_data):
        result = {}
        result["pharse"] = DataField(self.已形成)
        result["all_d_point"] = DataField([])
        start = PointField()
        start.open = k_data['open'] / (1 + D_POINT_LENGTH)
        result['now_d_point'] = DataField([start, PointField()])
        result["start_point"] = start
        result["is_ready"] = DataField(True)  # 是否已经运行到过200 50日线上

        # 该字段不需要，因为已形成结束的条件就是运行到 200 50 线下
        # result["is_down_ready"] = DataField(False) # 形成后是否运行到过200 50日线下
        return result

    def parse_pharse(self):
        yt_pharse = self.pre_data["pre_pharse"]

        # pharse 用到is ready 提前计算
        if self.now_k_data['high'] > self.MA(200) and self.now_k_data['high'] > self.MA(50) and \
                self.now_k_data['high'] > self.MA(10) or self.now_k_data['high'] > self.MA(20):
            self.now_data["is_ready"] = True

        # D类失效导致起点更新，会影响判断D类形成，提前计算
        if self.now_data['all_d_point'].data:
            # 如果收盘加超过最后（最低）一个D类，则从后往前遍历所有D类，删除被覆盖的D类，并记录所有D类的起点，
            # 选出最低的起点再与当前起点比较，如果更低则替换
            if self.now_k_data['close'] >= self.now_data['all_d_point'].data[-1][1].close:
                low_start = self.now_data['all_d_point'].data[-1][0]
                for n, d_point in enumerate(self.now_data['all_d_point'].data[:-1]):
                    d_point = self.now_data['all_d_point'].data[-(n+2)]
                    if d_point.data[0].open < low_start.open:
                        low_start = d_point.data[0]
                    else:
                        break
                self.now_data['all_d_point'].data = self.now_data['all_d_point'].data[:-(n+1)]
                if self.now_data['start_point'] is not None:
                    # 如果start是None说明已经形成D类，下次到达50 200 日线下时形成新的起点
                    if low_start.open < self.now_data['start_point'].open:
                        self.now_data['start_point'] = low_start

        if yt_pharse == self.已形成:
            if self.now_k_data['high'] < self.MA(200) or self.now_k_data['high'] < self.MA(50):
                self.now_data['parse'].data = self.均线下

                self.now_data['all_d_points'].data.append(self.now_data['now_d_point'])
                self.now_data['start_point'] = PointField()
                self.now_data['is_ready'].data = False
                self.now_data['now_d_point'] = None

        else:
            if self.now_k_data['is_ready'].data:
                if self.now_k_data['close'] > self.MA(200) and self.now_k_data['close'] > self.MA(50):
                    if self.now_k_data['close'] / self.now_data["start_point"].open >= (1 + D_POINT_LENGTH):
                        self.now_data['parse'] = self.已形成

                        self.now_data['now_d_point'] = DataField([self.now_data["start_point"], PointField()])
                        self.now_data['start_point'] = None

            elif self.now_k_data['high'] < self.MA(200) or self.now_k_data['high'] < self.MA(50):
                self.now_data['parse'].data = self.均线下
            elif self.now_k_data['high'] > self.MA(200) or self.now_k_data['high'] > self.MA(50):
                self.now_data['parse'].data = self.均线上
            else:
                self.now_data['parse'].data = self.均线中

    def parse_start_point(self):
        """
        如果当天重新设置了最低D类，且仍未形成（需要起点），新最低起点的起点参与竞争起点
        如果当天形成，则之前的起点就不再需要了，重置起点，向下运行
        如果创新低，且有起点则更新起点
        :return:
        """
        td_pharse = self.now_data["pharse"].data

        # 不需要再pharse前处理，因为如果发生，一定不会形成，对pharse无影响
        # todo: 有没有可能，比地点低，但是却在50 200 日线上？  应该几乎不会发生
        if not td_pharse == self.已形成 and self.now_data['start_point'] is not None:
            if self.now_k_data['open'] < self.now_data['start_point'].open:
                self.now_data['start_point'] = PointField()

    def parse_is_ready(self):
        """
        在形成后，第一次下跌到50 200日线下时重置
        只要到达过一次，所有均线上，就永久有效
        :return:
        """

    def parse_now_d_point(self):
        """
        距离上次D类高点，到达过所有均线上方，且距离上次D类高点后的低点上涨超过15%，则形成新的D类高点
        D类高点形成后，如果创新高，D类高点也会持续更新
        :return:
        """
        td_pharse = self.now_data["pharse"].data

        if td_pharse == self.已形成:
            if self.now_k_data["close"] > self.now_data['now_d_point'].data[0].close:
                self.now_data['now_d_point'].data[1] = PointField()

    def parse_all_d_point(self):
        """
        如果收盘加超过最后（最低）一个D类，则从后往前遍历所有D类，删除被覆盖的D类，并记录所有D类的起点，
        选出最低的起点再与当前起点比较，如果更低则替换
        :return:
        """
