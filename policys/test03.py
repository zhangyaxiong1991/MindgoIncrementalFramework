# coding: utf-8

import datetime
import functools

from normal_styles.daily.dl_0106 import DLUpDownScore


def get_stock_grade(stock_data, style_data):
    return style_data['step_1d'].iloc[0][DLUpDownScore.column_name]

def handle_stock_grade(stock_grade):
    stock_grade_list = [(k, v) for k, v  in stock_grade.items()]
    stock_grade_list.sort(key=lambda x: x[1])
    log.info("正100：", stock_grade_list[:100])
    log.info("反100：", stock_grade_list[-100:])


def init(account):
    # 设置要交易的证券(600519.SH 贵州茅台)
    account.security = '000001.SH'
    account.date = datetime.datetime.strptime('2020-01-03', '%Y-%m-%d')
    account.stocks = list(get_all_securities('stock', '20190807').index)
    account.styles = [DLUpDownScore(up_ranges=[[pd._libs.tslib.Timestamp('2019-11-23'), pd._libs.tslib.Timestamp('2019-12-20')],
                                               [pd._libs.tslib.Timestamp('2019-12-23'), pd._libs.tslib.Timestamp('2020-01-06')]
                                               ],
                                    ),
                      ]
    account.stock_data_range = {'1d': ('20190807', '20200106')}
    account.stock_grade = {}


def before_trading(account):
    pass


def after_trading(account):
    now = get_datetime()
    if not now.date() == account.date.date():
        log.info(now, now.date(), account.date.date())
        return

    all_columns = functools.reduce(lambda x, y: x + y, [i.column_names for i in account.styles])
    for stock in account.stocks:
        stock_data = {}
        style_data = {}
        for step in account.stock_data_range:
            step_stock_data = get_price([stock], account.stock_data_range[step][0], account.stock_data_range[step][1], step, ['close', 'open', 'low', 'high'])[stock]
            step_style_data = pd.DataFrame(index=step_stock_data.index, columns=all_columns)
            stock_data['step_' + step] = step_stock_data
            style_data['step_' + step] = step_style_data
            for style in account.styles:
                style.set_data(step_stock_data, step_style_data)
        account.stock_grade[stock] = get_stock_grade(stock_data, style_data)

    handle_stock_grade(account.stock_grade)


def handle_data(account, data):
    # 获取证券过去20日的收盘价数据
    pass
