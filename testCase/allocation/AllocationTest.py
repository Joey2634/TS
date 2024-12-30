import os
import pandas as pd
from configs.Database import mysql


def loadStrategyConfig(env, strategy_ids):
    """
    读取策略参数
    """
    with mysql(env, cursor_type='dict') as cursor:
        sql = "select strategy_id, business_type, security_selection_id, " \
              "white_list_id, risk_id, asset_allocation_id " \
              "from strategy_config  where strategy_id in {0} ".format(tuple(strategy_ids))
        cursor.execute(sql)
        data = cursor.fetchall()
        return data

if __name__ == '__main__':
    # print(os.path.abspath('.'))
    data1 = pd.read_csv('/home/lr/Desktop/position.csv')
    data2 = pd.read_csv('/home/lr/Desktop/position2.csv')
    # data = data.pivot('strategy_id','indicator_name','indicator_value')
    data = pd.merge(data1,data2,on=['trade_date','windcode'],how='outer')
    data.to_csv('/home/lr/Desktop/perfor.csv')