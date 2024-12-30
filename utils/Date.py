"""
公共函数
"""
from rediscluster import RedisCluster
from configs.Redis import *
from configs.Database import *
# redis_cli = RedisCluster(startup_nodes=prod, password='citics')


def storeCalendar(exchmarket='SSE'):
    """wind拿交易日历"""
    sql = "select TRADE_DAYS from wind.ASHARECALENDAR where S_INFO_EXCHMARKET = '{}' order by TRADE_DAYS".format(
        exchmarket)
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    tradedays = [d[0] for d in data]
    redis_cli.set('ASHARECALENDAR', tradedays.__str__())
    return tradedays


def getTradeDates(start_date='20111101', end_date='20111101', exchmarket='SSE'):
    """ 获取交易日历"""
    # start_date = time.strftime('%Y%m%d', time.strptime(start_date, '%Y-%m-%d'))
    # end_date = time.strftime('%Y%m%d', time.strptime(end_date, '%Y-%m-%d'))
    dateseq = getRedisTradeDates()
    dateseq = sorted(dateseq)
    tradedays = dateseq[_getBiggerIndex(start_date, dateseq):_getLowerIndex(end_date, dateseq) + 1]
    # return [time.strftime('%Y-%m-%d', time.strptime(date, '%Y%m%d')) for date in tradedays]
    return tradedays


def _getLowerIndex(date, dateseq: list):
    for i in range(len(dateseq) - 1, 0, -1):
        if dateseq[i] <= date:
            return i


def _getBiggerIndex(date, dateseq):
    for i in range(len(dateseq) - 1):
        if dateseq[i] >= date:
            return i


def getRedisTradeDates(exchmarket='SSE'):
    "KEY= ASHARECALENDAR"
    data = redis_cli.get('ASHARECALENDAR')
    if data:
        return eval(data)
    else:
        return storeCalendar(exchmarket)


# 查询交易日区间
# section为正数获取日期之后交易日，为负数获取日期之前的交易日
def getTradeSectionDates(time_data, section):
    """查询交易日区间"""
    # time_data = time.strftime('%Y%m%d', time.strptime(time_data, '%Y-%m-%d'))
    time_data = time_data.replace("-", "")
    dateseq = getRedisTradeDates()
    dateseq = sorted(dateseq)
    if section > 0:
        index_date = _getBiggerIndex(time_data, dateseq)
        tradedays = dateseq[index_date:index_date + section]
    else:
        index_date = _getLowerIndex(time_data, dateseq)
        tradedays = dateseq[index_date + section + 1:index_date + 1]
    # return [time.strftime('%Y-%m-%d', time.strptime(date, '%Y%m%d')) for date in tradedays]
    return tradedays



if __name__ == '__main__':
    # print(getTradeSectionDates('20201219',-2))
    # stopInfo = redis_cli.hget(ConditionRedisKey,'STOP')
    # stopInfo = eval(stopInfo)
    pass