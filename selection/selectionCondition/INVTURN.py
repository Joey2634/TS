from selection.selectionCondition.SELECTION_CONDITION import *


class INVTURN(SelectionCondition):
    """
    中信一级行业中，存货周转率
    """

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)

    def getData(self):
        oracle = Database(WIND_DB)
        if self.threshold.endswith('TD'):
            self.day_head = getTradeSectionDates(self.current_day, int(self.threshold[:-2])-1)[0]
            sql = ""
        else:
            sql ="select S_INFO_WINDCODE from" \
                 "(select a.S_INFO_WINDCODE,ROW_NUMBER() OVER(partition by ind order by S_FA_INVTURN desc) RN," \
                 "count(*) over(partition by ind) as n_rows,a.S_FA_INVTURN,b.ind " \
                 "from (select S_INFO_WINDCODE, ANN_DT, S_FA_INVTURN " \
                 "from wind.AShareFinancialIndicator where (S_INFO_WINDCODE, ANN_DT, REPORT_PERIOD) in " \
                 "(select S_INFO_WINDCODE, max(ANN_DT), max(REPORT_PERIOD) from wind.AShareFinancialIndicator " \
                 "where ANN_DT <= '{}' group by S_INFO_WINDCODE) and s_info_windcode not in " \
                 "(select s_info_windcode from asharest where (s_type_st = 'T' or s_type_st = 'Z' or s_type_st = 'L') " \
                 "and entry_dt <= '{}' and (remove_dt > '{}' or REMOVE_DT is NULL)) and s_info_windcode not in " \
                 "(select s_info_windcode from asharetradingsuspension where s_dq_suspenddate = '{}') " \
                 "and s_info_windcode in (select s_info_windcode from ashareeodprices where trade_dt='{}')" \
                 "and s_info_windcode in (select distinct S_CON_WINDCODE FROM wind.Aindexmembers" \
                  " where S_INFO_WINDCODE in {} and s_con_indate<={} and (s_con_outdate>{} or s_con_outdate is NULL ))) a " \
                 "left join " \
                 "(select *from (select S_INFO_WINDCODE, ind, ENTRY_DT, REMOVE_DT " \
                 "from (select S_INFO_WINDCODE,substr(citics_ind_code, 1, 4) ind,ENTRY_DT,REMOVE_DT " \
                 "from wind.AShareIndustriesClassCITICS)) where ENTRY_DT <= '{}' and " \
                 "(REMOVE_DT > '{}' or REMOVE_DT is NULL)) b on a.S_INFO_WINDCODE =b.S_INFO_WINDCODE " \
                 "where ENTRY_DT is not NULL and a.S_FA_INVTURN is not null) where RN{}round(n_rows*{}/100)"\
                .format(self.day, self.day, self.day,self.day, self.day, self.security_pool,
                        self.day, self.day, self.day, self.day, self.symbol, self.threshold)
        t = time.time()
        print('start excute and fetch..')
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
        print('fetch done, time spend', time.time()-t)
        # 返回的标的池list
        codes = list(map(lambda x: x[0], data))
        oracle.cursor.close()
        oracle.conn.close()
        return sorted(codes)

    def getSecurityPool(self, selection_condition):
        for i in self.trade_dates:
            self.current_day = i
            self.security_pool = tuple(selection_condition.split(':')[1].split(','))
            self.day = getTradeSectionDates(i, (self.d1 - 1))[0]  # 获取所求日日期
            print(i, '{}:从WIND数据库获取数据中...'.format(selection_condition))
            self.codes_dict[i] = self.getData()  # 筛选后的code
        return self.codes_dict

    def setSecurityPool(self, codes_dict, selection_condition):
        condition_key, sp,condition_value = selection_condition.split(':')
        condition_key = condition_key + ':' + sp
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




