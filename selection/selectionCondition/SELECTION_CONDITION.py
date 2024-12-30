from utils.Date import *
import time


class SelectionCondition:

    def __init__(self, parameters, start_date, end_date, env, mode):
        """
        :param parameters: [-1TD,>=,20]  or [-1TD,>=,-10TD]
        :param security_pool_dict: {'20200916':['600030.SH','300033.SH']}当日总股票池
        """
        super().__init__()
        if not parameters[0].startswith('SECURITY_POOL'):
            self.d1, self.symbol, self.threshold = parameters
            if self.d1.endswith('TD'):
                self.d1 = int(self.d1[:-2])
            elif self.d1 == 'SD':
                self.d1 = 0
        else:
            # 'security_pool', '000906.SH'
            self.d1, self.threshold = parameters[0].split(':')
            self.thresholds = self.threshold.split(',')
        self.env = env
        self.mode = mode
        self.codes_dict = {}
        self.start_date = start_date
        self.end_date = end_date
        self.trade_dates = getTradeDates(self.start_date, self.end_date)
        # 根据环境选择redis
        self.redisCli = RedisCluster(startup_nodes=redis_client_dict[self.env], password='citics')
        # 存条件指标数值的dict
        self.final_dict = {}

    def insertMysql(self, res_list, condition_key, condition_value):
        """
        筛选条件插入函数
        """
        db = Database(AI_DB[self.env])
        sql_del = """delete from single_factor_security_pool where condition_key='{}' and condition_value='{}' and trade_date>='{}' and trade_date<='{}'"""\
            .format(condition_key, condition_value, self.start_date, self.end_date)
        db.cursor.execute(sql_del)
        sql_ins = """insert into single_factor_security_pool values (%s,%s,%s,%s)"""
        db.cursor.executemany(sql_ins, res_list)
        db.conn.commit()
        db.cursor.close()
        db.conn.close()

    def setConditionRate(self, condition_prefix, final_dict):
        # 存redis
        if self.redisCli.hexists(ConditionRedisKey, str(condition_prefix)):
            condition_redis = eval(self.redisCli.hget(ConditionRedisKey, str(condition_prefix)))
            condition_redis.update(final_dict)
            self.redisCli.hset(ConditionRedisKey, str(condition_prefix), str(condition_redis))
        else:
            self.redisCli.hset(ConditionRedisKey, str(condition_prefix), str(final_dict))
        print('条件指标', condition_prefix, '更新到redis中...')



