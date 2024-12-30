from selection.selectionCondition.SELECTION_CONDITION import *


class PE_2_1Y_AVG_PE(SelectionCondition):
    """
    市盈率PE/过去一年市盈率PE的均值_PIT[-1TD] <= 1.34
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        oracle = Database(WIND_DB)
        # 过去一年
        self.n_day_head = getTradeSectionDates(self.current_day, (-251))[0]
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            # 过去一年
            self.b_day_head = getTradeSectionDates(self.day_head, (-251))[0]
            sql = "select * from " \
                  "(select c.s_info_windcode,d.PE/c.avge as rate from " \
                  "(select a.s_info_windcode, avg(a.PE) as avge from " \
                  "(select s_info_windcode, trade_dt, s_val_pe_TTM as PE " \
                  "from ashareeodderivativeindicator) a right join " \
                  "(select trade_days as trade_dt from asharecalendar" \
                  " where s_info_exchmarket = 'SSE' and trade_days <= '{}' and trade_days >= '{}') b " \
                  "on a.trade_dt = b.trade_dt group by a.s_info_windcode) c " \
                  "left join (select s_info_windcode,s_val_pe_TTM as PE from wind.ashareeodderivativeindicator " \
                  "where (S_INFO_WINDCODE,trade_dt) in (select * from (select S_INFO_WINDCODE,max(TRADE_DT) dt from wind.ashareeodderivativeindicator " \
                  "WHERE TRADE_DT<= '{}' and trade_dt>='{}' and s_val_pe_TTM is not NULL " \
                  "GROUP BY S_INFO_WINDCODE ORDER BY S_INFO_WINDCODE,dt DESC ))) d " \
                  "on c.s_info_windcode =d.s_info_windcode) aa left join " \
                  "(select c.s_info_windcode,d.PE/c.avge as rate from " \
                  "(select a.s_info_windcode, avg(a.PE) as avge from " \
                  "(select s_info_windcode, trade_dt, s_val_pe_TTM as PE " \
                  "from ashareeodderivativeindicator) a right join " \
                  "(select trade_days as trade_dt from asharecalendar" \
                  " where s_info_exchmarket = 'SSE' and trade_days <= '{}' and trade_days >= '{}') b " \
                  "on a.trade_dt = b.trade_dt group by a.s_info_windcode) c " \
                  "left join (select s_info_windcode,s_val_pe_TTM as PE from " \
                  "ashareeodderivativeindicator where trade_dt = '{}') d " \
                  "on c.s_info_windcode =d.s_info_windcode) bb on aa.s_info_windcode=bb.s_info_windcode " \
                  "where aa.rate {} bb.rate" \
                .format(self.day, self.n_day_head, self.m_day, self.day, self.day_head, self.b_day_head, self.day_head,
                        self.symbol)
        else:
            sql = "select * from (select c.s_info_windcode,d.PE/c.avge as rate from (select a.s_info_windcode, avg(a.PE) as avge from " \
                  "(select s_info_windcode, trade_dt, s_val_pe_TTM as PE from ashareeodderivativeindicator" \
                  ") a right join (select trade_days as trade_dt from asharecalendar" \
                  " where s_info_exchmarket = 'SSE' and trade_days <= '{}' and trade_days >= '{}') b on a.trade_dt = b.trade_dt " \
                  "group by a.s_info_windcode) c left join (select s_info_windcode,s_val_pe_TTM as PE from wind.ashareeodderivativeindicator " \
                  "where (S_INFO_WINDCODE,trade_dt) in (select * from (select S_INFO_WINDCODE,max(TRADE_DT) dt from wind.ashareeodderivativeindicator " \
                  "WHERE TRADE_DT<= '{}' and trade_dt>='{}' and s_val_pe_TTM is not NULL " \
                  "GROUP BY S_INFO_WINDCODE ORDER BY S_INFO_WINDCODE,dt DESC ))) d " \
                  "on c.s_info_windcode =d.s_info_windcode) where rate {} {}" \
                .format(self.m_day, self.n_day_head, self.m_day, self.day, self.symbol, self.threshold)
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
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
            print(i, 'PE_2_1Y_AVG_PE:从WIND数据库获取数据中...')
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




