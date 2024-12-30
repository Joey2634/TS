from datetime import datetime
from configs.Database import mysql
import csv
from utils.Date import getTradeSectionDates


def initAccountAndAsset(env='dev',strategy_ids=[],start_run_day=''):
    strategy_ids = str(strategy_ids).replace("[","").replace("]","")
    with mysql(env, None, True) as cursor:
        cursor.execute("select strategy_id,amount from strategy_config where strategy_id in ({})".format(strategy_ids))
        strategy_info = list(cursor.fetchall())
        account_info = [[i[0], start_run_day, 'CASH', 0, i[1], i[1], i[1]] for i in strategy_info]
        asset_info = [[i[0], start_run_day, 0, i[1], i[1], i[1], 0, 1] for i in strategy_info]
        insertToDb(cursor, 'account', account_info, strategy_ids)
        insertToDb(cursor, 'asset', asset_info, strategy_ids)

def insertToDb(cursor,table,data,strategy_ids,delete=True):
    values = str(('%s',) * len(data[0])).replace("'", "")
    if delete:
        cursor.execute("delete from {} where strategy_id in ({})".format(table,strategy_ids))
    cursor.executemany("insert into {} values {}".format(table, values), data)

def createStrategyConfig(env='dev', strategy_configs_file='create_strategy_config.csv'):
    with open(strategy_configs_file, mode='r') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        next(csv_reader)
        strategy_config_list = []
        for row in csv_reader:
            row = [i.strip() for i in row] #删除空格
            strategy_config_list.append(tuple([i for i in row]))
    strategy_config_list = list(set(strategy_config_list))
    values = str(('%s',) * len(strategy_config_list[0])).replace("'", "")
    with mysql(env, None, True) as curser:
        curser.executemany("insert into strategy_config VALUES {}".format(values), strategy_config_list)



if __name__ == '__main__':
    createStrategyConfig('dev')

    # pre_day = getTradeSectionDates(datetime.strftime(datetime.now(), '%Y%m%d'), -2)[0]
    # initAccountAndAsset(strategy_ids=['S-L-5|LastPrice|AVERAGE|RISK-24',
    #                                   'S-L-5|MarketValue|OPEN|RISK-24'],start_run_day=pre_day)
