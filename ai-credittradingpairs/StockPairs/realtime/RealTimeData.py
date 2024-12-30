# -*- coding: utf-8 -*-

'''
@Project : PyCharm
@File : RealTimeData.py
@Contact : cuiweijian@citics.com
@author : Simon
@Date : 2020/11/3
@AddTime 下午4:05
'''

import redis
from StockPairs.utils.Redis import redis_config_dev

redis_pool_prod_bak = redis.ConnectionPool(host=redis_config_dev[0], db=int(redis_config_dev[1]),
                                           port=int(redis_config_dev[2]), password=redis_config_dev[3])

def getRealTimeData(wind_code):
    redis_cli = redis.StrictRedis(connection_pool=redis_pool_prod_bak)
    predata = redis_cli.lrange(wind_code, 0, 0)
    return eval(predata[0])

def getRealTimeNewPrice(wind_code):
    redis_cli = redis.StrictRedis(connection_pool=redis_pool_prod_bak)
    predata = redis_cli.lrange(wind_code, 0, 0)
    data = eval(predata[0])
    return data['lastPrice']/10000


if __name__ == '__main__':
    getRealTimeNewPrice('600030.SH')