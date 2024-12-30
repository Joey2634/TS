from AI_Data.queryDBData import getTradeDates
from configs.Database import *
import datetime
from configs.Redis import redisCli


def getFromMysql(table, asset_allocation_id, start_date, end_date):
    """
    从mysql取出黑白名单
    :return:date_dict
    """
    db = Database(AI_DB[MOCK])
    sql = """select trade_date, windcode from '{}' where asset_allocation_id='{}' and trade_date>='{}' and trade_date<='{}' """ \
        .format(table+'_his', asset_allocation_id, start_date, end_date)
    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    date_dict = {}
    for (trade_date, windcode) in data:
        if date_dict.__contains__(trade_date):
            date_dict[trade_date].append(windcode)
        else:
            date_dict[trade_date] = [windcode]
    return date_dict


def run(table, start_date, end_date, asset_allocation_id):
    """
    黑、白名单toRedis
    """
    res_dict = {}
    date_list = getTradeDates(start_date, end_date)
    for i in date_list:
        res_dict[i] = []
    table_codes = getFromMysql(table, start_date, end_date, asset_allocation_id)
    res_dict.update(table_codes)
    redisCli.hset('ai-investment-manager|'+table, 'ai-investment-manager|'+table+'|'+asset_allocation_id, str(res_dict))


if __name__ == '__main__':
    table = 'white_list'
    # table = 'black_list'
    start_date = '2015-01-05'
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    asset_allocation_id = 'S-L-1|WB|MarketPrice'
    run(table, start_date, end_date, asset_allocation_id)












