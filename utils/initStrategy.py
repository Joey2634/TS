import traceback
from datetime import datetime
from configs.Database import mysql, DEV, Database, AI_DB
from utils.Date import getTradeSectionDates


def getStrategyAmount(env, strategy_ids: list):
    """
    读取策略参数
    """
    sql = "select strategy_id, amount from strategy_config where strategy_id "
    if len(strategy_ids) > 1:
        strategy_ids = tuple(strategy_ids)
        sql = sql + "in {0}".format(tuple(strategy_ids))
    elif len(strategy_ids) == 1:
        sql = sql + "= '{0}'".format(strategy_ids[0])
    else:
        exit("No strategy_id")
    with mysql(env, 'dict') as cursor:
        cursor.execute(sql)
        res = cursor.fetchall()
    return res


def setAssetAndAccount(trade_date, strategy_configs, future_ratio=0):
    """
    初始化trade_date和trade_date上一个交易日的asset和account,期货策略和非期货策略分开初始化
    :param trade_date:
    :param strategy_configs:
    :param future_ratio: 期货账户初始化资金占比
    :return:
    """
    date_list = getTradeSectionDates(trade_date, -2)
    result = {'asset': [[strategy_config['strategy_id'], trade_date, 0, strategy_config['amount'],
                         strategy_config['amount'], strategy_config['amount'], 0, 1, 1] for strategy_config in
                        strategy_configs for trade_date in date_list]}
    if future_ratio == 0:
        result['account'] = [[strategy_config['strategy_id'], trade_date, 'CASH', 0, strategy_config['amount'],
                              strategy_config['amount'], strategy_config['amount']] for strategy_config in
                             strategy_configs for trade_date in date_list]
    else:
        result['account'] = [
            [strategy_config['strategy_id'], trade_date, 'FUTURE', 0, strategy_config['amount'] * future_ratio,
             strategy_config['amount'] * future_ratio, strategy_config['amount'] * future_ratio] for strategy_config in
            strategy_configs for trade_date in date_list]
        cash_ratio = 1 - future_ratio
        result['account'].extend(
            [[strategy_config['strategy_id'], trade_date, 'CASH', 0, strategy_config['amount'] * cash_ratio,
              strategy_config['amount'] * cash_ratio, strategy_config['amount'] * cash_ratio] for strategy_config in
             strategy_configs for trade_date in date_list])
    strategy_ids = [i['strategy_id'] for i in strategy_configs]
    with mysql(env, commit=True) as cursor:
        for table, data in result.items():
            if not data:
                continue
            try:
                values = str(('%s',) * len(data[0])).replace("'", "")
                cursor.execute("delete from {} where strategy_id in ({})".format(table, str(strategy_ids).replace("[",
                                                                                                                  "").replace(
                    "]", "")))
                cursor.executemany("insert into {} values {}".format(table, values), data)
            except:
                print("store data error:table:{},error:{}".format(table, traceback.format_exc()))


def delete_strategy(strategy_id, env=DEV):
    tables = ['target_position', 'adjusted_target_position', 'asset', 'account',
              'position', 'trade', 'target_order', 'performance', 'period_performance']
    DB = Database(AI_DB[env])
    strategy_id = str(strategy_id).replace("[", "").replace("]", "")
    for table in tables:
        try:
            DB.cursor.execute("delete from {} where strategy_id in ({})".format(table, strategy_id))
            DB.conn.commit()
            print(table, 'delete success!')
        except Exception as e:
            print(table, e)
    DB.cursor.close()
    DB.conn.close()


if __name__ == '__main__':
    today = datetime.now().strftime('%Y%m%d')
    env = 'dev'
    strategy_ids = ['S-L-4|LastPrice|CLOSE|RISK-169']
    # delete_strategy(strategy_ids, env=DEV)
    strategy_configs = getStrategyAmount(env, strategy_ids)
    setAssetAndAccount(today, strategy_configs, future_ratio=0.1)
