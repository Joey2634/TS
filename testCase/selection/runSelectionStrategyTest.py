import multiprocessing
from selection.SecuritySelection import *

"""
手动执行
selection 入口

"""


def resetStrategyRedis(security_selection_id, start_date, end_date):
    """
    如果redis数据被清，但是mysql存在数据
    :param security_selection_id: 选股策略id
    :param start_date: 起始日期
    :param end_date: 结束日期
    """
    db = Database(AI_DB[DEV])
    sql = """select trade_date, windcode from security_pool where security_selection_id='{}' and trade_date>='{}' and trade_date<='{}'""" \
        .format(security_selection_id, start_date, end_date)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    db.cursor.close()
    db.conn.close()
    date_dict = {}
    for (trade_date, windcode) in data:
        if date_dict.__contains__(trade_date):
            date_dict[trade_date].append(windcode)
        else:
            date_dict[trade_date] = [windcode]
    # 存redis
    redisCli = RedisCluster(startup_nodes=redis_cluster_prod, password='citics')
    if redisCli.hexists(StrategyRedisKey, str(security_selection_id)):
        condition_redis = eval(redisCli.hget(StrategyRedisKey, str(security_selection_id)))
        condition_redis.update(date_dict)
        redisCli.hset(StrategyRedisKey, str(security_selection_id), str(condition_redis))
    else:
        redisCli.hset(StrategyRedisKey, str(security_selection_id), str(date_dict))


def resetConditionRedis(condition, start_date, end_date):
    """
    如果redis数据被清，但是mysql存在数据
    :param condition: 条件
    :param start_date: 起始日期
    :param end_date: 结束日期
    """
    template, para = condition.split(':')
    db = Database(AI_DB[DEV])
    sql = """select trade_date, windcode from single_factor_security_pool where  condition_key='{}' and condition_value='{}' and trade_date>='{}' and trade_date<='{}'""" \
        .format(template, para, start_date, end_date)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    db.cursor.close()
    db.conn.close()
    date_dict = {}
    for (trade_date, windcode) in data:
        if date_dict.__contains__(trade_date):
            date_dict[trade_date].append(windcode)
        else:
            date_dict[trade_date] = [windcode]
    # 存redis
    redisCli = RedisCluster(startup_nodes=redis_cluster_prod, password='citics')
    if redisCli.hexists(ConditionRedisKey, str(condition)):
        condition_redis = eval(redisCli.hget(ConditionRedisKey, str(condition)))
        condition_redis.update(date_dict)
        redisCli.hset(ConditionRedisKey, str(condition), str(condition_redis))
    else:
        redisCli.hset(ConditionRedisKey, str(condition), str(date_dict))


def runSelectionCondition(condition, start_date, end_date):
    """
    更新条件筛选结果
    :param condition: 条件
    :param start_date: 起始日期
    :param end_date: 结束日期
    """
    template, para = condition.split(':')
    para_list = para.split(',')
    env = DEV
    ob = FuncName[template](para_list, start_date, end_date, env)
    res_dict = ob.getSecurityPool()
    ob.setSecurityPool(res_dict, condition)


def runSelectionStrategy(security_selection_id, start_date, end_date):
    """
    筛选选股策略标的池
    :param security_selection_id: 选股策略str
    :param start_date: 起始日期(定时任务--当日)
    :param end_date: 结束日期(定时任务--当日)
    """
    env = DEV
    security_selection = SecuritySelection(security_selection_id, start_date, end_date, env)
    security_selection.setSecurityPool()


def multiRun(func, selection_id_list, start_date, end_date):
    """
    多进程调用函数
    :param func: 函数
    :param selection_id_list: 选股策略list
    :param start_date: 起始日期(定时任务--当日)
    :param end_date: 结束日期(定时任务--当日)

    """
    result = []
    pool = multiprocessing.Pool()
    for each in selection_id_list:
        result.append(pool.apply_async(func, (each, start_date, end_date)))
    pool.close()
    pool.join()
    for r in result:
        r.get()


def run(security_selection_id_list, start_date, end_date, overwrite_condition):
    """
    更新策略或条件结果
    :param security_selection_id_list: 选股策略list
    :param start_date: 起始日期
    :param end_date: 结束日期
    :param overwrite_condition: 重刷的条件
    :return:
    """
    if overwrite_condition != []:
        multiRun(runSelectionCondition, overwrite_condition, start_date, end_date)
    multiRun(runSelectionStrategy, security_selection_id_list, start_date, end_date)


if __name__ == '__main__':
    # 1.设置选股策略🆔id
    selection_id_list = ['S-L-3']
    # 起止日期
    start_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = '2015-01-05'
    end_date = datetime.date.today().strftime("%Y-%m-%d")

    # 重刷的条件
    overwrite_condition = ['EPS_GROWTH_RATE:SD,>=,-9TD']
    overwrite_condition = []
    # 2.run
    run(selection_id_list, start_date, end_date, overwrite_condition)

    # mysql有数据，redis没有或不全 mysql-->redis
    # m2r_selection_id_list = ['S-L-3']
    # m2r_condition_list = ['EPS_GROWTH_RATE:SD,>=,-9TD']
    # multiRun(resetStrategyRedis, m2r_selection_id_list, start_date, end_date)
    # multiRun(resetConditionRedis, m2r_condition_list, start_date, end_date)









