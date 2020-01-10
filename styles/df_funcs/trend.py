# coding:utf-8

TREND_上涨 = 3
TREND_平上涨 = 1
TREND_平 = 0
TREND_平下跌 = -1
TREND_下跌 = -3


def set_trend(stock_data, column_name='k_trend'):
    df = pd.DataFrame([[]], index=stock_data.index)
    df = pd.merge(df, stock_data, how='left', left_index=True, right_index=True)
    if column_name not in df.columns:
        df[column_name] = TREND_平

    for i in range(len(df.index)):
        if i == 0:
            pre = None
        else:
            pre = df.iloc[i-1]
        now = df.iloc[i]

        if pre is None:
            now[column_name] = TREND_平

        if pre is not None:
            log.info(now['high'], pre['high'], now['low'], pre['low'], pre[column_name])
            if pre[column_name] == TREND_上涨 or pre[column_name] == TREND_平上涨:
                if now['high'] > pre['high']:
                    now[column_name] = TREND_上涨
                elif now['low'] < pre['low']:
                    now[column_name] = TREND_下跌
                else:
                    now[column_name] = TREND_平上涨

            elif pre[column_name] == TREND_下跌 or pre[column_name] == TREND_平下跌:
                if now['low'] < pre['low']:
                    now[column_name] = TREND_下跌
                elif now['high'] > pre['high']:
                    now[column_name] = TREND_上涨
                else:
                    now[column_name] = TREND_平下跌

            else:
                if now['low'] < pre['low'] and now['high'] > pre['high']:
                    now[column_name] = TREND_平
                elif now['low'] < pre['low']:
                    now[column_name] = TREND_下跌
                elif now['high'] > pre['high']:
                    now[column_name] = TREND_上涨
                else:
                    now[column_name] = TREND_平
