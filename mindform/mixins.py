# coding:utf-8

class MAMixin:
    def MA(self, count):
        return self.styles.stock_cache_data.iloc[-count:]["close"].mean()

    def up_break_mas(self, mas):
        """
        收盘价在均线上方
        :param mas:
        :return:
        """
        assert isinstance(mas, list)
        for ma in mas:
            if ma > self.styles.cache_data_num:
                raise Exception("均线天数必须小于{}".format(self.styles.cache_data_num))
            if not self.td_k_data["close"] > self.MA(ma):
                return False
        return True
