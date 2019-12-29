# coding:utf-8


class Trend:
    column_name = 'k_trend'
    
    上涨 = '3'
    平上涨 = '1'
    平 = '0'
    平下跌 = '-1'
    下跌 = '-3'
    
    def set_data(self, stock_data, style_data):
        if Trend.column_name not in style_data.columns:
            style_data[Trend.column_name] = Trend.平

        for i in range(len(stock_data.index)):
            if i == 0:
                pre = None
                pre_style = None
            else:
                pre = stock_data.iloc[i - 1]
                pre_style = style_data.iloc[i - 1]
            now = stock_data.iloc[i]
            now_style = style_data.iloc[i]

            if pre is not None:
                if pre_style[Trend.column_name] == Trend.上涨 or pre_style[Trend.column_name] == Trend.平上涨:
                    if now['high'] > pre['high']:
                        now_style[Trend.column_name] = Trend.上涨
                    elif now['low'] < pre['low']:
                        now_style[Trend.column_name] = Trend.下跌
                    else:
                        now_style[Trend.column_name] = Trend.平上涨

                elif pre_style[Trend.column_name] == Trend.下跌 or pre_style[Trend.column_name] == Trend.平下跌:
                    if now['low'] < pre['low']:
                        now_style[Trend.column_name] = Trend.下跌
                    elif now['high'] > pre['high']:
                        now_style[Trend.column_name] = Trend.上涨
                    else:
                        now_style[Trend.column_name] = Trend.平下跌

                else:
                    if now['low'] < pre['low'] and now['high'] > pre['high']:
                        now_style[Trend.column_name] = Trend.平
                    elif now['low'] < pre['low']:
                        now_style[Trend.column_name] = Trend.下跌
                    elif now['high'] > pre['high']:
                        now_style[Trend.column_name] = Trend.上涨
                    else:
                        now_style[Trend.column_name] = Trend.平
