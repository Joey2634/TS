from selection.selectionCondition.SELECTION_CONDITION import *
import datetime
from dateutil.relativedelta import relativedelta


class ROIC(SelectionCondition):
    """
    投入资本回报率
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        oracle = Database(WIND_DB)
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            sql = "select s_info_windcode, minu from " \
                  "(select a.s_info_windcode, rate1- rate2 as minu from " \
                  "(select s_info_windcode, S_FA_ROIC rate1 from wind.AShareFinancialIndicator " \
                  "where (s_info_windcode, ann_dt, report_period) in " \
                  "(select s_info_windcode, max(ann_dt), max(report_period) from wind.AShareFinancialIndicator " \
                  "where ann_dt <= '{}' group by s_info_windcode)) a " \
                  "left join " \
                  "(select s_info_windcode, S_FA_ROIC rate2 from wind.AShareFinancialIndicator " \
                  "where (s_info_windcode, ann_dt, report_period) in " \
                  "(select s_info_windcode, max(ann_dt), max(report_period) from wind.AShareFinancialIndicator " \
                  "where ann_dt <= '{}' group by s_info_windcode)) b " \
                  "on a.s_info_windcode = b.s_info_windcode) d " \
                  "on c.s_info_windcode = d.s_info_windcode) where minu {} 0" \
                .format(self.day, self.day_head, self.symbol)

        else:
            sql ="select s_info_windcode, S_FA_ROIC from wind.AShareFinancialIndicator " \
                 "where (s_info_windcode, ann_dt, report_period) in " \
                 "(select s_info_windcode, max(ann_dt), max(report_period) from wind.AShareFinancialIndicator " \
                 "where ann_dt <= '{}' group by s_info_windcode) and S_FA_ROIC {} {}"\
                .format(self.day, self.symbol, self.threshold)
        t = time.time()
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
        print('fetch done, time spend', time.time()-t)
        # 返回的标的池list
        codes = list(data)
        oracle.cursor.close()
        oracle.conn.close()
        return sorted(codes)

    def getSecurityPool(self, selection_condition):
        condition_prefix = selection_condition.split(',')[0]
        for date in self.trade_dates:
            self.final_dict[date] = {}
        for i in self.trade_dates:
            self.current_day = i
            if str(self.d1).endswith('Y'):
                day = (datetime.datetime.strptime(i, "%Y%m%d") - relativedelta(years=-int(self.d1[:-1]))).strftime(
                    '%Y%m%d')  # 获取所求日 前一日/年日期
                self.day = getTradeSectionDates(day, -1)[0]
                print(i, 'ROIC:从WIND数据库获取数据中...')
            else:
                self.day = getTradeSectionDates(i, (self.d1 - 1))[0]  # 获取所求日 前一日/年日期
                print(i, 'ROIC:从WIND数据库获取数据中...')
            codes_res = self.getData()  # 筛选后的code
            for (code, rate) in codes_res:
                self.final_dict[i][code] = rate
            self.codes_dict[i] = [i[0] for i in codes_res]
        # 将条件指标存入redis
        # self.setConditionRate(condition_prefix, self.final_dict)
        return self.codes_dict

    def setSecurityPool(self, codes_dict, selection_condition):
        condition_key, condition_value = selection_condition.split(':')
        res_list = sum(list(map(lambda x: [[x, condition_key, condition_value, i] for i in codes_dict[x]], self.trade_dates)), [])
        print('条件', selection_condition, '存入mysql中...')
        self.insertMysql(res_list, condition_key, condition_value)
        # 存redis
        if self.redisCli.hexists(ConditionRedisKey, str(selection_condition)):
            condition_redis = eval(self.redisCli.hget(ConditionRedisKey, str(selection_condition)))
            condition_redis.update(codes_dict)
            self.redisCli.hset(ConditionRedisKey, str(selection_condition), str(condition_redis))
        else:
            self.redisCli.hset(ConditionRedisKey, str(selection_condition), str(codes_dict))
        print('条件', selection_condition, '更新到redis中...')


if __name__ == '__main__':
    years = ['2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015',
             '2016', '2017', '2018', '2019', '2020', '2021']
    for i in years:
        start = i + '0101'
        if i == '2021':
            end = '20210319'
        else:
            end = i + '1231'
        a = ROIC(['-2Y', '>=', '13'], start, end, 'dev', 'backtest')
        codes_dict = a.getSecurityPool('ROIC:-2Y,>=,13')
        a.setSecurityPool(codes_dict, 'ROIC:-2Y,>=,13')
        print(1)
    # a = ROIC(['-1TD', '>=', '20'], '20150105', '20210202', 'dev', 'backtest')
    # codes_dict = a.getSecurityPool('ROIC:-1TD,>=,20')
    # a.setSecurityPool(codes_dict, 'ROIC:-1TD,>=,20')
    # print(1)

