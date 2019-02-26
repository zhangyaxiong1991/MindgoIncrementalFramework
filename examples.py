from mindform import MindForm
from mindform import models

mf = MindForm(device="SH.000001")

class PharseModel:
    """
    this: 当天数据(k线 + 自定义字段)
    pre:  前一天数据
    """
    ma = [] # 默认没有任何均线
    k_fields = [] # 没有除了默认k线数据外的其他数据


class Form01(models.PharseModel):
    pharse = {"pharse_01": "阶段01",
              "pharse_02": "阶段02",
              "pharse_03": "阶段03"
              }

    pharse_change = {
        ("pharse_01", "pharse_02"): "对应规则",
        ("pharse_02", "pharse_03"): "对应规则",
    }

    field_01 = models.PointField()

    def pharse_change_pharse_01_pharse_02(self,):
        '''
        pharse_change中设置都都必须实现，并且所有的转换规则互斥，每天会调用所有的转换规则
        '''
        pass

    def pharse_change_pharse_02_pharse_03(self,):
        pass

    def after_change_pharse_02_pharse_03(self):
        """
        时机：切换后
        :return:
        """
        pass

    def before_change_pharse_02_pharse_03(self):
        """
        时机：切换前
        :return:
        """
        pass

    def parse_field_01(self):
        """
        切换完成后分析字段，按字段定义顺序调用
        :return:
        """
        pass

    def parse(self):
        """"
        切换完成后整体分析，在单个字段调用完后调用
        :return:
        """
        pass

    def before_pharse_change(self):
        """
        在字段切换前调用
        :return:
        """
        pass

mf.regist(Form01)

def on_bar():
    for stock in mf.stocks:
        if mf["form01"][stock].this["field01"] > 0:
            pass
    