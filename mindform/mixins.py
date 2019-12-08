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
            if not self.now_k_data["close"] > self.MA(ma):
                return False
        return True
    
    def 阴加速(self):
        if (self.close < self.open and self.pre_close < self.pre_open and (self.open / self.close) > (self.pre_open / self.pre_close)):
            return True
        return False

    def 向下跳空(self):
        if self.now_k_data['high'] < self.pre_k_data['low']:
            return True
        return False

    def 阴线(self):
        if self.now_k_data.close < self.now_k_data.open:
            return True
        return False

    def 周期内高点(self, target, start, end):
        if isinstance(start, int):
            date = self.styles.stock_cache_data.iloc[start: end][target].idxmax()
            return date, self.styles.stock_cache_data.iloc[date]
        else:
            date = self.styles.stock_cache_data.loc[start: end][target].argmax()
            return date, self.styles.stock_cache_data.loc[date]

    def 周期内低点(self, target, start, end):
        if isinstance(start, int):
            date = self.styles.stock_cache_data.iloc[start: end][target].idxmin()
            return date, self.styles.stock_cache_data.iloc[date]
        else:
            date = self.styles.stock_cache_data.loc[start: end][target].argmin()
            return date, self.styles.stock_cache_data.loc[date]


