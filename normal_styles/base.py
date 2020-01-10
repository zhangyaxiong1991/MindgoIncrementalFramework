# coding:utf-8


class BaseStyle:
    def add_column_data(self, df, column_name, value):
        for i in range(len(df.index)):
            df.iloc[i][column_name] = value

    def get_column_names(self):
        return "{}_{}".format(self.__class__.__name__, self.name)
