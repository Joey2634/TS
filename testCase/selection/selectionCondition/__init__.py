from configs.Database import *


def getMysql(selection_condition, start_date, end_date, env):
    """
    从mysql取出条件筛选的codes
    :return:date_dict
    """
    condition_key, condition_value = selection_condition.split(':')
    db = Database(AI_DB[env])
    sql = """select trade_date, windcode from single_factor_security_pool where condition_key='{}' and condition_value='{}' and trade_date>='{}' and trade_date<='{}' """ \
        .format(condition_key, condition_value, start_date, end_date)
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
    return date_dict

