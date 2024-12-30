from selection.selectionCondition.SELECTION_CONDITION import *
import pandas as pd
import datetime


class NETPROFIT_1M_VAL(SelectionCondition):
    """
    一致预测净利润 30天变化率
    ((最新一致预测值/1月前一致预测值)-1)*100
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        """暂时不支持与天数比较"""
        oracle = Database(WIND_DB)
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            sql = ""
        else:
            # 得到30天前日期
            day_before_1m = (datetime.datetime.strptime(self.current_day, '%Y%m%d') +
                             datetime.timedelta(days=-30)).strftime('%Y%m%d')
            self.day_before_1m = getTradeSectionDates(day_before_1m, -1)[0]
            sql = "select EST_DT,S_INFO_WINDCODE,NET_PROFIT,ROLLING_TYPE,BENCHMARK_YR from wind.AShareConsensusRollingData " \
                  "where (EST_DT='{}'OR EST_DT='{}') and ROLLING_TYPE in ('FY1', 'FY2', 'FY3')"\
                .format(self.day, self.day_before_1m)
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
        oracle.cursor.close()
        oracle.conn.close()
        # 日期，标的，净利润，类型，基准年度
        df = pd.DataFrame(data=data, columns=['EST_DT', 'S_INFO_WINDCODE', 'NET_PROFIT', 'ROLLING_TYPE', 'BENCHMARK_YR'])
        df = df[~df['BENCHMARK_YR'].isna()]
        # 基准年度与当前年份的差值绝对值
        df['BENCHMARK_MINUS'] = df['BENCHMARK_YR'].apply(lambda x: abs(int(x[:4]) - int(self.day[:4])))
        # 类型结尾数值(FY 1 2 3)
        df['ROLLING_TYPE_END'] = df['ROLLING_TYPE'].apply(lambda x: int(x[-1]))
        # 以上二者相等的数据  即预测的年份相同
        df_res = df[df['BENCHMARK_MINUS'] == df['ROLLING_TYPE_END']]
        df_final = pd.merge(df_res[df_res['EST_DT'] == self.day_before_1m], df_res[df_res['EST_DT'] == self.day],
                            on=['S_INFO_WINDCODE'])
        # 计算30天变化率
        df_final['res'] = ((df_final['NET_PROFIT_y']/df_final['NET_PROFIT_x'])-1)*100
        df_final['res'] = df_final['res'].astype(float)
        # df config配置条件筛选
        con = pd.Series(list(map(lambda x: eval("'{}' {} '{}'".format(x, self.symbol, float(self.threshold))),
                                 df_final['res'])))
        df_final = df_final[con]
        df_final = df_final[~df_final['res'].isna()]
        return df_final[['S_INFO_WINDCODE', 'res']].values.tolist()

    def getSecurityPool(self, selection_condition):
        condition_prefix = selection_condition.split(',')[0]
        for date in self.trade_dates:
            self.final_dict[date] = {}
        for i in self.trade_dates:
            self.current_day = i
            self.day = getTradeSectionDates(i, (self.d1 - 1))[0]  # 获取所求日日期
            # 实盘取定时任务前最新数据
            if self.mode == 'backtest':
                self.m_day = self.day
            else:
                self.m_day = self.current_day
            print(i, 'NETPROFIT_1M_VAL:从WIND数据库获取数据中...')
            t =time.time()
            codes_res = self.getData()  # 筛选后的code
            print('time spend ', time.time()-t)
            for (code, rate) in codes_res:
                self.final_dict[i][code] = rate
            self.codes_dict[i] = list(set([i[0] for i in codes_res]))
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
    years = ['2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014',
             '2015', '2016', '2017', '2018', '2019', '2020', '2021']
    for i in years:
        start = i + '0101'
        if i == '2021':
            end = '20210414'
        else:
            end = i + '1231'
        a = NETPROFIT_1M_VAL(['-1TD', '>=', '0'], start, end, 'dev', 'backtest')
        codes_dict = a.getSecurityPool('NETPROFIT_1M_VAL:-1TD,>=,0')
        a.setSecurityPool(codes_dict, 'NETPROFIT_1M_VAL:-1TD,>=,0')
        print(1)




