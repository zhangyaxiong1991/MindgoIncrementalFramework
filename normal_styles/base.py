# coding:utf-8


class BaseStyle:
    LOW = -1
    HIGH = 1

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.step = kwargs['step']

    def add_column_data(self, df, column_name, value):
        for i in range(len(df.index)):
            df.iloc[i][column_name] = value

    def get_all_columns(self):
        return []

    @staticmethod
    def get_min_index(ser, range):
        indexs = [i for i in ser.index if range[0] <= i <= range[1]]
        if len(indexs) == 0:
            return None
        return ser.loc[indexs].argmin()

    @staticmethod
    def get_max_index(ser, range):
        indexs = [i for i in ser.index if range[0] <= i <= range[1]]
        if len(indexs) == 0:
            return None
        return ser.loc[indexs].argmax()

    def group_str(self):
        return "{}:{}-{}".format(self.__class__.__name__, self.start, self.end)
