from selection.selectionCondition.SELECTION_CONDITION import *


class OIPS(SelectionCondition):
    """
    每股营业收入
    每股营业收入_PIT[选股当日(SD)] >= 每股营业收入_PIT[-12TD]
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        oracle = Database(WIND_DB)
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            sql = "select s_info_windcode, minu from " \
                  "(select c.s_info_windcode,orps1- orps2 as minu from " \
                  "(select a.s_info_windcode, rev / tot_shr as orps1 from " \
                  "(select s_info_windcode, oper_rev_ttm as rev from asharettmhis " \
                  "where (s_info_windcode, ann_dt, report_period) in " \
                  "(select s_info_windcode, max(ann_dt), max(report_period) from asharettmhis " \
                  "where ann_dt <= '{}' group by s_info_windcode)) a " \
                  "left join " \
                  "(select s_info_windcode, tot_shr from asharecapitalization " \
                  "where (s_info_windcode, change_dt) in " \
                  "(select s_info_windcode, max(change_dt) " \
                  "from asharecapitalization " \
                  "where change_dt <= '{}' group by s_info_windcode)) b " \
                  "on a.s_info_windcode = b.s_info_windcode) c " \
                  "left join " \
                  "(select a.s_info_windcode, rev / tot_shr as orps2 from " \
                  "(select s_info_windcode, oper_rev_ttm as rev from asharettmhis " \
                  "where (s_info_windcode, ann_dt, report_period) in " \
                  "(select s_info_windcode, max(ann_dt), max(report_period) from asharettmhis " \
                  "where ann_dt <= '{}' group by s_info_windcode)) a " \
                  "left join " \
                  "(select s_info_windcode, tot_shr from asharecapitalization " \
                  "where (s_info_windcode, change_dt) in " \
                  "(select s_info_windcode, max(change_dt) " \
                  "from asharecapitalization " \
                  "where change_dt <= '{}'group by s_info_windcode)) b " \
                  "on a.s_info_windcode = b.s_info_windcode) d " \
                  "on c.s_info_windcode = d.s_info_windcode) where minu {} 0" \
                .format(self.m_day, self.m_day, self.day_head, self.day_head, self.symbol)
        else:
            sql ="SELECT s_info_windcode, orps from " \
                 "(select a.s_info_windcode, rev / tot_shr as orps from " \
                 "(select s_info_windcode, oper_rev_ttm as rev from asharettmhis " \
                 "where (s_info_windcode, ann_dt, report_period) in " \
                 "(select s_info_windcode, max(ann_dt), max(report_period) from asharettmhis " \
                 "where ann_dt <= '{}' group by s_info_windcode)) a " \
                 "left join " \
                 "(select s_info_windcode, tot_shr from asharecapitalization" \
                 " where (s_info_windcode, change_dt) in " \
                 "(select s_info_windcode, max(change_dt) " \
                 "from asharecapitalization " \
                 "where change_dt <= '{}'group by s_info_windcode)) b " \
                 "on a.s_info_windcode = b.s_info_windcode) where orps {} {}"\
                .format(self.m_day, self.m_day, self.symbol, self.threshold)
        oracle.cursor.execute(sql)
        t = time.time()
        print('start fetch..')
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
            self.day = getTradeSectionDates(i, (self.d1 - 1))[0]  # 获取所求日日期
            # 实盘取定时任务前最新数据
            if self.mode == 'backtest':
                self.m_day = self.day
            else:
                self.m_day = self.current_day
            print(i, 'OIPS:从WIND数据库获取数据中...')
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
    # mode = 'backtest'
    mode = 'live'
    a = OIPS(['-1TD','>=', '-9TD'], '20210426', '20210426','dev', mode)
    codes_dict = a.getSecurityPool('OIPS:-1TD,>=,-9TD')
    a.setSecurityPool(codes_dict, 'OIPS:-1TD,>=,-9TD')
    print(1)

