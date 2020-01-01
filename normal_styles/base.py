# coding:utf-8


class BaseStyle:
    def add_column_data(self, df, column_name, value):
        df[column_name] = pd.Series([value] * len(df.index), index=df.index)
