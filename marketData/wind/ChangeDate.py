import datetime
from rediscluster import RedisCluster
from configs.Database import *
from configs.Redis import *
from utils.Date import *
import time


def insertMysql(env, res_list, condition_key, condition_value, start_date, end_date):
    """
    筛选条件插入函数
    """
    # start_date = datetime.datetime.strftime(datetime.datetime.strptime(start_date, '%Y%m%d'), '%Y-%m-%d')
    # end_date = datetime.datetime.strftime(datetime.datetime.strptime(end_date, '%Y%m%d'), '%Y-%m-%d')
    db = Database(AI_DB[env])
    # sql_del = """delete from ai_investment_manager.single_factor_security_pool_ where condition_key='{}' and condition_value='{}' and trade_date>='{}' and trade_date<='{}'""" \
    #     .format(condition_key, condition_value, start_date, end_date)
    # db.cursor.execute(sql_del)
    sql_ins = """insert into ai_investment_manager.single_factor_security_pool_ values (%s,%s,%s,%s)"""
    db.cursor.executemany(sql_ins, res_list)
    db.conn.commit()
    db.cursor.close()
    db.conn.close()


def strategyInsertMysql(env, security_selection_id, rescodes_dict, start_date, end_date):
    """
    策略标的池存mysql
    """
    db = Database(AI_DB[env])
    sql_del = """delete from ai_investment_manager.security_pool where security_selection_id='{}'"""\
        .format(security_selection_id)
    db.cursor.execute(sql_del)
    date_list = sorted(rescodes_dict.keys())
    res_list = sum(list(map(lambda x: [[security_selection_id, x, code] for code in rescodes_dict[x]], date_list)), [])
    sql_ins = """insert into ai_investment_manager.security_pool values (%s,%s,%s)"""
    db.cursor.executemany(sql_ins, res_list)
    db.conn.commit()
    db.cursor.close()
    db.conn.close()


if __name__ == '__main__':
    env = 'dev'
    # env = 'prod'
    redis_cli = RedisCluster(startup_nodes=redis_client_dict[env], password='citics')
    redis_cli_dev = RedisCluster(startup_nodes=redis_client_dict['dev'], password='citics')

    # # 条件
    # conditions = redis_cli_dev.hkeys(ConditionRedisKey)
    # for condition in conditions:
    #     codes_dict = eval(redis_cli.hget(ConditionRedisKey, condition))
    #     res = {}
    #     for i in codes_dict:
    #         ii = datetime.datetime.strftime(datetime.datetime.strptime(i, '%Y-%m-%d'), '%Y%m%d')
    #         res[ii] = codes_dict[i]
    #     redis_cli.hset(ConditionRedisKey, condition, str(res))
    #
    #     start_date = min(res.keys())
    #     end_date = max(res.keys())
    #     #
    #     # trade_dates = getTradeDates(start_date, end_date)
    #     #
    #     # condition_key, condition_value = condition.decode().split(':')
    #     # res_list = sum(list(map(lambda x: [[x, condition_key, condition_value, i] for i in res[x]], trade_dates)), [])
    #     # # insertMysql(env, res_list, condition_key, condition_value, start_date, end_date)
    #     print(conditions.index(condition), condition.decode(), start_date, '~~~', end_date, '---done---')
    print('---------------------------------')

    # 策略
    strategy_id = redis_cli_dev.hkeys(StrategyRedisKey)
    strategy_id.remove(b'S-L-5')
    for id in strategy_id:
        codes_dict = eval(redis_cli.hget(StrategyRedisKey, id))
        # res = {}
        # for i in codes_dict:
        #     ii = datetime.datetime.strftime(datetime.datetime.strptime(i, '%Y-%m-%d'), '%Y%m%d')
        #     res[ii] = codes_dict[i]
        # redis_cli.hset(StrategyRedisKey, id, str(res))

        res = codes_dict
        start_date = min(res.keys())
        end_date = max(res.keys())
        trade_dates = getTradeDates(start_date, end_date)
        # strategyInsertMysql(env, id.decode(), res, start_date, end_date)

        print(strategy_id.index(id), id.decode(), '~~~', '---done---', len(res))







