from selection.selectionCondition.SELECTION_CONDITION import *


class REVS5(SelectionCondition):
    """
    过去5日的价格动量
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        oracle = Database(WIND_DB)
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            sql = "select a.S_INFO_WINDCODE, a.S_TECH_REVS5 from " \
                  "(select * from wind.RevenueTechnicalFactor where TRADE_DT='{}' and S_TECH_REVS5 is not null) a " \
                  "left join " \
                  "(select * from wind.RevenueTechnicalFactor where TRADE_DT='{}' and S_TECH_REVS5 is not null) b " \
                  "on a.S_INFO_WINDCODE=b.S_INFO_WINDCODE where a.S_TECH_REVS5 {} b.S_TECH_REVS5"\
                .format(self.day, self.day_head, self.symbol)
        else:
            # sql = "select S_INFO_WINDCODE, S_TECH_REVS5 from wind.RevenueTechnicalFactor where TRADE_DT='{}' " \
            #       "and S_TECH_REVS5 is not null " \
            #       "and S_TECH_REVS5 {} {}"\
            #     .format(self.day, self.symbol, self.threshold)
            sql = "select S_INFO_WINDCODE, S_TECH_REVS5 from wind.RevenueTechnicalFactor " \
                  "where (S_INFO_WINDCODE, TRADE_DT) in (select * from " \
                  "(select S_INFO_WINDCODE, max(TRADE_DT) dt from wind.RevenueTechnicalFactor " \
                  "where trade_dt<='{}' and TRADE_DT>='{}' group by S_INFO_WINDCODE " \
                  "order by S_INFO_WINDCODE,dt desc)) and S_TECH_REVS5 is not null and S_TECH_REVS5 {} {}"\
                .format(self.m_day, self.day, self.symbol, self.threshold)
        t = time.time()
        print('start excute and fetch..')
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
        print('fetch done, time spend', time.time()-t)
        # 返回的标的池list
        codes = list(data)
        oracle.cursor.close()
        oracle.conn.close()
        return codes

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
            print(i, 'REVS5:从WIND数据库获取数据中...')
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
    mode = 'backtest'
    # mode = 'live'
    a = REVS5(['-1TD','>=', '0.88'], '20210426', '20210426', 'dev', mode)
    codes_dict = a.getSecurityPool('REVS5:-1TD,>=,0.88')
    a.setSecurityPool(codes_dict, 'REVS5:-1TD,>=,0.88')
    print(1)

