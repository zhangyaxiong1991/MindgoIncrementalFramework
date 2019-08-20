# coding:utf-8

from collections import OrderedDict
import datetime

from mindform.basestyle import Style, StyleField, BaseField


class Styles(object):
    def __init__(self, driver, follow_stocks, start_date):
        Style.styles = self
        StyleField.styles = self
        BaseField.styles = self
        self.start_date = start_date
        self._driver = driver  # 驱动个股

        # 关注的股票
        self._follow_stocks = follow_stocks

        # 注册的形态
        self._styles = None

        # 用户形态数据  {"个股代码": {"形态名": {"字段名": 字段值}}}
        self._style_data = {}
        self._pre_style_data = {}

        # 缓存的所有个股的数据
        self.stocks_cache_data = {}
        self.stock_cache_data = None

        self.fileds = ['close', 'open', 'low', 'high']
        
        self.td = None
        self.last_two_days_data = None
        self.last_two_days_data_refresh_date = None
        self.all_stocks = None
        self.all_stocks_refresh_date = None
        self.cache_data_num = None

        self.now_stock = None
        self.now_style = None
        self.now_denpend_styles = None
        self.now_k_data = None
        self.pre_k_dta = None

    def get_stock_all_history_data(self, stock, now=None):
        start_date = self.start_date
        if now is None:
            now = self.td
        data = get_price([stock], start_date.strftime("%Y%m%d"), now.strftime("%Y%m%d"), '1d', self.fileds)
        return data.get(stock)

    def regist(self, styles):
        if not self._styles is None:
            raise Exception('只能注册一次形态')
        self._styles = OrderedDict()
        styles = list(set(styles))
        assert len(styles) > 0
        styles = [i if isinstance(i, Style) else i() for i in styles]
        for i in styles:
            assert isinstance(i, Style)
        styles = set(styles)
        while 1:
            if len(styles) == 0:
                break
            hit_style = []
            not_registed_style = []
            not_hited_style = []
            for style in styles:
                style_not_registed_style = []
                style_not_hited_style = []
                for _, depend_style in style.__depends__.items():
                    if depend_style.__name__ in self._styles:  # 已分配
                        continue
                    elif depend_style not in styles: # 未注册
                        style_not_registed_style.append(depend_style)
                    else: # 已注册，但仍未分配，可能该形态太存在依赖
                        style_not_hited_style.append(depend_style)

                not_registed_style += style_not_registed_style
                not_hited_style += style_not_hited_style

                if not (style_not_registed_style or style_not_hited_style):
                    hit_style.append(style)

            if not hit_style and not not_registed_style:
                raise Exception('存在循环依赖{}'.format(styles))
            if hit_style:
                for i in hit_style:
                    styles.remove(i)
                    self._styles[i.__name__] = i
            if not_registed_style:
                for i in not_registed_style:
                    styles.add(i)
        self.cache_data_num = 2
        for style_name, style in self._styles.items():
            for depend_style in style.__depends__:
                setattr(style, depend_style, self._styles[depend_style])
            if style.__catch_data_num__ > self.cache_data_num:
                self.cache_data_num = style.__catch_data_num__

    def get_all_stocks(self):
        """
        获取所有关注的个股
        :return:
        """
        if self.all_stocks_refresh_date is None or self.all_stocks_refresh_date == self.td:
            try:
                self.all_stocks = self._follow_stocks()
            except TypeError:
                self.all_stocks =  self._follow_stocks
            self.all_stocks_refresh_date = self.td
        return self.all_stocks

    def _handle_rights(self, stock, all_history_data):
        for style_name, style in self._styles.items():
            style.handle_rights(stock, all_history_data)

    def set_td_date(self):
        """
        设置当天时间
        :return:
        """
        td = datetime.datetime.strptime(get_datetime().strftime("%Y%m%d"), "%Y%m%d")
        if self.td == td:
            return
        if self.td is None:
            self.td = td
            self.yt = None
        else:
            self.yt = self.td
            self.td = td


    def down_load_last_two_days_data(self):
        """
        下载最近两天的数据,检查是否需要复权，如果需要则触发复权的逻辑，并且更新缓存的个股数据
        :return:
        """
        if self.last_two_days_data_refresh_date is None or not self.last_two_days_data_refresh_date == self.td:
            self.last_two_days_data_refresh_date = self.td
            if self.start_date > self.td:
                log.info("还未到达框架起始时间，不下载任何数据")
                self.last_two_days_data = {}
                self.stocks_cache_data = {}
            else:
                all_stocks = self.get_all_stocks()
                if self.start_date == self.td:
                    log.info("正好是起始时间，只请求一天的数据")
                    self.last_two_days_data = get_candle_stick(all_stocks + [self._driver], self.td.strftime("%Y%m%d"),
                                                               fre_step="1d", fields=self.fileds,
                                                               skip_paused=True, bar_count=1)
                    self.stocks_cache_data = self.last_two_days_data
                else:
                    log.info("超过起始时间，请求两天的数据")
                    self.last_two_days_data = get_candle_stick(all_stocks + [self._driver], self.td.strftime("%Y%m%d"),
                                                               fre_step="1d", fields=self.fileds,
                                                               skip_paused=True, bar_count=2)
                    for stock, last_two_days_data in self.last_two_days_data.items():
                        if not self.td in last_two_days_data.index:
                            # 当天停盘
                            log.info("{} 停盘 日期：{}, 下载数据：{}".format(stock, self.td, last_two_days_data))
                            continue
                        # 剔除掉小于起始时间的数据
                        last_two_days_data.drop([i for i in last_two_days_data.index if i < self.start_date], inplace=True)
                        if len(last_two_days_data) == 1:
                            log.info("{} 上市日期，只下载到一天的数据".format(stock))
                            self.stocks_cache_data[stock] = last_two_days_data
                        else:
                            if stock not in self.stocks_cache_data:
                                raise ValueError("data not catched: {}".format(stock))
                            if not self.stocks_cache_data[stock].index[-1] == last_two_days_data.index[0]:
                                raise ValueError("data not right, _catch_data last date:{} yt date: {}"
                                                 .format(self.stocks_cache_data[stock].index[-1], last_two_days_data.index[0]))
                            if not self.stocks_cache_data[stock].iloc[-1]["close"] == last_two_days_data.iloc[0]["close"]:
                                # 需要复权，先拿着所有历史数据去对让形态数据复权，然后裁剪后赋值给缓存数据
                                log.info("{} 发生复权 \n缓存的最后一天数据：{}\n 下载的前一天数据：{}"
                                         .format(stock, self.stocks_cache_data[stock].iloc[-1]["close"], last_two_days_data.iloc[0]["close"]))
                                stock_all_history_data = self.get_stock_all_history_data(stock)
                                missed_date = set(self.stocks_cache_data[stock].index) - set(stock_all_history_data.index)
                                if missed_date:
                                    raise ValueError("some data missed when get all history data stock:{} missed date:{}"
                                                     .format(stock, missed_date))
                                self._handle_rights(stock, stock_all_history_data)
                                catch_data_first_data = self.stocks_cache_data[stock].index[0]
                                stock_all_history_data.drop([i for i in stock_all_history_data.index if i < catch_data_first_data], inplace=True)
                                self.stocks_cache_data[stock] = stock_all_history_data
                            else:
                                log.info("{} 未复权 简单缓存最后一天的数据".format(stock))
                                self.stocks_cache_data[stock] = self.stocks_cache_data[stock].append(last_two_days_data.iloc[1])
                    for stock, stock_catched_data in self.stocks_cache_data.items():
                        if len(stock_catched_data) > self.cache_data_num:
                            # 缓存数据超长时删除第一行即可
                            stock_catched_data.drop(stock_catched_data.index[0], inplace=True)

    def get_stock_last_two_days_date(self, stock):
        """
        获取个股最近两天的数据
        :param stock:
        :return:
        """
        self.down_load_last_two_days_data()
        return self.last_two_days_data.get(stock, None)

    def set_now_stock(self, stock):
        self.now_stock = stock

    def set_now_style(self, style_name):
        """
        向当前计算形态注入k线数据等
        :return:
        """
        self.now_style = self._styles[style_name]
        self.now_style.now_k_data = self.last_two_days_data[self.now_stock].iloc[-1]
        self.now_style.pre_k_dta = self.last_two_days_data[self.now_stock].iloc[0]
        self.now_k_data = self.last_two_days_data[self.now_stock].iloc[-1]
        self.pre_k_dta = self.last_two_days_data[self.now_stock].iloc[0]

    def set_depend_styles(self):
        """
        向当前计算形态注入依赖形态的数据
        :return:
        """
        for name in self.now_style.__depends__:
            self._styles[name].set_now_stock(self.now_stock)

    def run(self):
        """
        收盘逐个个股、按照依赖关系逐个计算形态计算数据
        :return:
        """
        if self.start_date > get_datetime():
            return
        self.set_td_date()

        log.info("开始计算{}形态数据".format(self.td))
        all_stocks = self.get_all_stocks()
        log.info("all_stocks: {}".format(all_stocks))

        self.down_load_last_two_days_data()

        for name in self._styles:
            log.info("计算形态:{} 数据".format(name))
            for stock in all_stocks:
                log.info("计算个股{} 数据".format(stock))
                # 还未上市
                if stock not in self.stocks_cache_data:
                    continue
                # 当天停盘
                if not self.td == self.stocks_cache_data[stock].index[-1]:
                    log.info("{}停盘，不计算形态数据".format(stock))
                    continue
                self.stock_cache_data = self.stocks_cache_data[stock]
                self.set_now_stock(stock)
                self.set_now_style(name)
                self.set_depend_styles()
                self.now_style.handle_data(stock, self.td, self.stocks_cache_data[stock].loc[self.td].to_dict())

    def before_trading_start(self, account):
        pass

    def handle_data(self, account, data):
        pass

    def after_trading_end(self, account):
        self.run()
