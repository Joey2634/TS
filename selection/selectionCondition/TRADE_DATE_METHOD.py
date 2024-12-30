import datetime
from utils.Date import *


class TRADE_DATE_METHOD:
    """
    筛选交易日期方法
    """
    def __init__(self, start_date, end_date, condition):
        """
        :param start_date:开始日期
        :param end_date:结束日期
        :param condition: 交易日期条件
        :return: trade_dates 交易日期list
        """
        self.start_date = start_date
        self.end_date = end_date
        self.trade_dates = getTradeDates(start_date, end_date)
        self.condition = condition

    def getTradeDates(self):
        if self.condition.startswith('DATE_SKEWING'):
            trade_dates = self.dateSkewing(self.condition)
            return trade_dates

    def dateSkewing(self, condition):
        tempalte, date_skewings = condition.split('=')
        date_skewings = date_skewings.split(',')
        res_list = []
        for date_skewing in date_skewings:
            res = self.isTrade(date_skewing)
            res_list = res_list + res
        res_list = sorted(set(res_list))
        return res_list

    def isTrade(self, date_skewing):
        # 偏移日
        date_skewing = int(date_skewing)
        res_list=[]
        for day in self.trade_dates.copy():
            day_date = datetime.datetime.strptime(day, '%Y%m%d').date()  # day (date)
            day_yes = day_date + datetime.timedelta(days=-1)  # day昨日 (date)
            day_ahead = getTradeSectionDates(day, -2)[0]  # day前一个交易日 (str)
            day_ahead_date = datetime.datetime.strptime(day_ahead, '%Y%m%d').date()  # day前一个交易日 (date)
            # day = 偏移日 True
            if day_date.weekday() == date_skewing:
                print('周', date_skewing+1, '为交易日时--', day, '是交易日')
                res_list.append(day)
            # day的昨天是休息日 & day>偏移日  True
            elif day_yes != day_ahead_date and day_date.weekday() >= date_skewing:
                print('周', date_skewing+1, '为交易日时--', day, '是交易日')
                res_list.append(day)
            else:
                print('周', date_skewing+1, '为交易日时--', day, '不是交易日,剔除...')
                # trade_dates.remove(day)
        return res_list

    def _getTradeDates(self):
        if self.condition.startswith('DATE_SKEWING'):
            trade_dates = self._dateSkewing(self.condition)
            return trade_dates

    def _dateSkewing(self, condition):
        tempalte, date_skewings = condition.split('=')
        date_skewings = date_skewings.split(',')
        res_list = []
        for date_skewing in date_skewings:
            res = self._isTrade(date_skewing)
            res_list = res_list + res
        res_list = sorted(set(res_list))
        return res_list

    def _isTrade(self, date_skewing):
        # 偏移日
        date_skewing = int(date_skewing)
        res_list=[]
        for day in self.trade_dates.copy():
            day_date = datetime.datetime.strptime(day, '%Y%m%d').date()  # day (date)
            day_yes = day_date + datetime.timedelta(days=-1)  # day昨日 (date)
            day_ahead = getTradeSectionDates(day, -2)[0]  # day前一个交易日 (str)
            day_ahead_date = datetime.datetime.strptime(day_ahead, '%Y%m%d').date()  # day前一个交易日 (date)
            # day = 偏移日 True
            if day_date.weekday() == date_skewing:
                # print('周', date_skewing+1, '为交易日时--', day, '是交易日')
                res_list.append(day)
            # day的昨天是休息日 & day>偏移日  True
            elif day_yes != day_ahead_date and day_date.weekday() >= date_skewing:
                # print('周', date_skewing+1, '为交易日时--', day, '是交易日')
                res_list.append(day)
            else:
                # print('周', date_skewing+1, '为交易日时--', day, '不是交易日,剔除...')
                # trade_dates.remove(day)
                pass
        return res_list






if __name__ == '__main__':
    d = TRADE_DATE_METHOD('20150101', '20150601', 'DATE_SKEWING=0')
    print(d.getTradeDates())









