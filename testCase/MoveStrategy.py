import pandas as pd
from configs.Database import *


def move_env(strategy_id,old_env,new_env):
    """
    策略迁移环境
    :param strategy_id:
    :param old_env:
    :param new_env:
    :return:
    """
    tables = ['target_position_backtest', 'adjusted_target_position_backtest', 'asset_backtest', 'account_backtest',
              'position_backtest', 'trade_backtest', 'target_order_backtest', 'performance_backtest','period_performance_backtest']
    tables2 = ['target_position', 'adjusted_target_position', 'asset', 'account', 'strategy_config',
              'position', 'trade', 'target_order', 'performance']
    oldDB = Database(AI_DB[old_env])
    newDB = Database(AI_DB[new_env])
    for table in tables2:
        try:
            oldDB.cursor.execute("select * from {} where strategy_id = '{}'".format(table, strategy_id))
            data = oldDB.cursor.fetchall()
            df = pd.DataFrame(list(data))
            values = ['%s' for _ in range(df.shape[1])]
            values = ','.join(values)
            newDB.cursor.execute("delete from {} where strategy_id='{}'".format(table, strategy_id))
            newDB.cursor.executemany("insert into {} values({})".format(table, values), data)
            newDB.conn.commit()
            print(table, 'move success!')
        except Exception as e:
            print(table, e)
    oldDB.cursor.close()
    oldDB.conn.close()
    newDB.cursor.close()
    newDB.conn.close()

def changeID(old_id,new_id,env):
    """
    用别的策略的数据覆盖其他策略的数据，重刷策略
    :param old_id:
    :param new_id:
    :param env:
    :return:
    """
    tables = ['target_position_backtest', 'adjusted_target_position_backtest', 'asset_backtest', 'account_backtest',
              'position_backtest', 'trade_backtest', 'target_order_backtest', 'performance_backtest','period_performance_backtest',
              'am_fee_backtest']
    tables2 = ['target_position', 'adjusted_target_position', 'asset', 'account',
               'position', 'trade', 'target_order', 'performance', 'am_fee']
    DB = Database(AI_DB[env],'dict')
    # with mysql(env, 'dict',commit=True) as cursor:
    for table in tables:
        try:
            DB.cursor.execute("select * from {} where strategy_id = '{}'".format(table, old_id))
            data = DB.cursor.fetchall()
            df = pd.DataFrame(data)
            df['strategy_id'] = new_id
            values = ['%s' for _ in range(df.shape[1])]
            values = ','.join(values)
            DB.cursor.execute("delete from {} where strategy_id='{}'".format(table, new_id))
            DB.cursor.executemany("insert into {} values({})".format(table, values), df.values.tolist())
            DB.conn.commit()
            print(table, 'move success!')
        except Exception as e:
            print(table, e)

def trans(strategy_id,env=DEV):
    """
    回测数据转为实盘数据
    :param strategy_id:
    :param env:
    :return:
    """
    table = {'target_position_backtest':'target_position', 'adjusted_target_position_backtest':'adjusted_target_position',
             'asset_backtest':'asset', 'account_backtest':'account', 'position_backtest':'position',
              'trade_backtest':'trade', 'target_order_backtest':'target_order', 'performance_backtest':'performance',
             'am_fee_backtest':'am_fee'}
    DB = Database(AI_DB[env])
    for key,value in table.items():
        try:
            DB.cursor.execute("select * from {} where strategy_id = '{}'".format(key, strategy_id))
            data = DB.cursor.fetchall()
            df = pd.DataFrame(list(data))
            values = ['%s' for _ in range(df.shape[1])]
            values = ','.join(values)
            DB.cursor.execute("delete from {} where strategy_id='{}'".format(value, strategy_id))
            DB.cursor.executemany("insert into {} values({})".format(value, values), data)
            DB.conn.commit()
            print(key, 'move success!')
        except Exception as e:
            print(table, e)
    DB.cursor.close()
    DB.conn.close()

def delete_strategy(strategy_id,env=DEV):
    tables = ['target_position_backtest', 'adjusted_target_position_backtest', 'asset_backtest', 'account_backtest',
              'position_backtest', 'trade_backtest', 'target_order_backtest', 'performance_backtest',
              'period_performance_backtest', 'target_position', 'adjusted_target_position', 'asset', 'account',
              'strategy_config', 'position', 'trade', 'target_order', 'performance','period_performance',
              'am_fee_backtest', 'am_fee', 'am_config', 'commission_rate']
    DB = Database(AI_DB[env])
    for table in tables:
        try:
            DB.cursor.execute("delete from {} where strategy_id='{}'".format(table, strategy_id))
            DB.conn.commit()
            print(table, 'delete success!')
        except Exception as e:
            print(table, e)
    DB.cursor.close()
    DB.conn.close()

if __name__ == '__main__':
    # changeID('S-L-16|LastPrice|CLOSE|RISK-44', 'turing_1-3', DEV)
    strategy_id = 'turing_3-1'
    # delete_strategy(strategy_id,PROD)
    old_env = DEV
    new_env = PROD
    move_env(strategy_id, old_env, new_env)
    # trans(strategy_id,env=DEV)