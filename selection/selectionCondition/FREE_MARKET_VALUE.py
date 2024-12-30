from selection.selectionCondition.SELECTION_CONDITION import *


class FREE_MARKET_VALUE(SelectionCondition):
    """
    自由流通市值
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        oracle = Database(WIND_DB)
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            sql = "select a.S_INFO_WINDCODE, a.fmv from " \
                  "(select S_INFO_WINDCODE, TRADE_DT, exp(S_DFA_LNFLOATMV) as fmv from wind.DailyValuationFactor " \
                  "where TRADE_DT='{}') a " \
                  "left join" \
                  "(select S_INFO_WINDCODE, TRADE_DT, exp(S_DFA_LNFLOATMV) as fmv from wind.DailyValuationFactor " \
                  "where TRADE_DT='{}') b " \
                  "on a.fmv {} b.fmv"\
                .format(self.day, self.day_head, self.symbol)
        else:
            sql = "select S_INFO_WINDCODE, fmv from " \
                  "(select S_INFO_WINDCODE, TRADE_DT, exp(S_DFA_LNFLOATMV) as fmv from wind.DailyValuationFactor) " \
                  "where TRADE_DT = '{}' and fmv {} {}"\
                .format(self.day, self.symbol, self.threshold)
        t = time.time()
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
        print('time spend', time.time()-t)
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
            print(i, 'FREE_MARKET_VALUE:从WIND数据库获取数据中...')
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



