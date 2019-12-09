# coding:utf-8
class MindformLogger:
    log = log
    log_date = None

    @staticmethod
    def info(*args):
        if MindformLogger.log_date is not None:
            if get_datetime() < MindformLogger.log_date:
                return
            log.info(*args)

    @staticmethod
    def warn(*args):
        if MindformLogger.log_date is not None:
            if get_datetime() < MindformLogger.log_date:
                return
            log.warn(*args)

    @staticmethod
    def error(*args):
        if MindformLogger.log_date is not None:
            if get_datetime() < MindformLogger.log_date:
                return
            log.error(*args)


class plt:
    get_all_securities = get_all_securities
    log = MindformLogger
    get_price = get_price
    get_datetime = get_datetime
    get_candle_stick = get_candle_stick
