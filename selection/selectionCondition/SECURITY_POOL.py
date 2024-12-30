import datetime

from selection.selectionCondition.SELECTION_CONDITION import *


class SECURITY_POOL(SelectionCondition):

    def __init__(self, paramaters, start_date, end_date, env, mode):
        super().__init__(paramaters, start_date, end_date, env, mode)
        self.redisCli = RedisCluster(startup_nodes=redis_client_dict[self.env], password='citics')
        self.paramaters = paramaters[0]

    def getSecurityPool(self, selection_condition):
        res_dict = {}
        for i in self.trade_dates:
            for t in self.thresholds:
                print('从wind获取{},{}数据中'.format(selection_condition, i))
                res_dict[i] = list(set(res_dict.get(i, []) + self.getData(t, i)))
        return res_dict

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

    def getData(self, security_index, trade_date):
        oracle = Database(WIND_DB)
        if security_index=='GGT100.WI':
            # 港股通100成份股
            sql = "select a.S_CON_WINDCODE from wind.AIndexMembersWIND a " \
                  "join wind.hksharedescription b on a.S_CON_WINDCODE = b.S_INFO_WINDCODE " \
                  "where a.F_INFO_WINDCODE = '{}' and a.cur_sign = '1'".format(security_index)
        else:
            sql = "select distinct S_CON_WINDCODE FROM wind.Aindexmembers" \
                  " where S_INFO_WINDCODE ='{}' and s_con_indate<={} and (s_con_outdate>{} or s_con_outdate is NULL )"\
                .format(security_index, trade_date, trade_date)
        oracle.cursor.execute(sql)
        data = oracle.cursor.fetchall()
        codes = list(map(lambda x: x[0], data))
        oracle.cursor.close()
        oracle.conn.close()
        return codes






