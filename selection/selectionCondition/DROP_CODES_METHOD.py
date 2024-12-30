import datetime
from utils.AiData import *


class DROP_CODES_METHOD:
    """
    剔除 ST,停牌 股票
    """
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.date_list = getTradeDates(self.start_date, self.end_date)

    def getStop(self):
        """
        获取停牌股票
        :return: stop_pool
        """
        stop_pool = dict()
        stop = getATotalStop(self.start_date, self.end_date)
        for day in self.date_list:
            stop_pool[day] = stop[stop['s_dq_suspenddate'] == day]['s_info_windcode'].values.tolist()
        return stop_pool

    def getST(self):
        """
        获取ST股票
        :return: st_pool
        """
        st_pool = dict()
        st = getATotalST(self.start_date)
        for day in self.date_list:
            st_ls = set(st[st['entry'] < day]['code']) - set(st[(st['entry'] < day) & (st['remove'] < day)]['code'])
            st_pool[day] = list(st_ls)
        return st_pool

    def getHKStop(self):
        """
        获取停牌股票
        :return: stop_pool
        """
        stop_pool = dict()
        stop = getHKTotalStop(self.start_date, self.end_date)
        for day in self.date_list:
            stop_pool[day] = stop[stop['s_dq_suspenddate'] == day]['s_info_windcode'].values.tolist()
        return stop_pool

    def getHKEnd(self):
        """
        获取退市股票
        :return: end_pool
        """
        end_pool = dict()
        end = getHKTotalEnd()
        for day in self.date_list:
            # 未来一个月会退市
            after = getTradeSectionDates(day, 21)[-1]
            # 获取当日已经退市 和 未来一个月会退市的股票
            end_pool[day] = end[end['s_delistdt'] <= after]['s_info_windcode'].values.tolist()
        return end_pool





