from configs.Database import mysql
import csv


def createAllocationConfig(env='dev', strategy_configs_file='create_strategy_config.csv'):
    with open(strategy_configs_file, mode='r') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        next(csv_reader)
        strategy_config_list = []
        for row in csv_reader:
            strategy_config_list.append(tuple(row))
    with mysql(env, None, True) as curser:
        sql = "insert into strategy_config (strategy_id, business_type, " \
              "security_selection_id, asset_allocation_id, algo_trading_id," \
              "white_list_id, risk_id, day_trading_id,amount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        curser.executemany(sql, strategy_config_list)


def loadAllocationConfig(env, strategy_ids):
    """
    读取策略参数
    """
    sql = "select * from strategy_config where strategy_id "
    with mysql(env, cursor_type='dict') as cursor:
        if len(strategy_ids) > 1:
            strategy_ids = tuple(strategy_ids)
            sql = sql + "in {0}".format(tuple(strategy_ids))
        else:
            sql = sql + "= '{0}'".format(strategy_ids[0])
        cursor.execute(sql)
        data = cursor.fetchall()
        print(data)
        return data


if __name__ == '__main__':
    loadStrategyConfig('dev', ['S-L-2|WB|MarketPrice2','S-L-2|WB|MarketPrice'])
