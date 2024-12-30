import datetime
from utils.Date import *
import arrow
import pandas as pd


def isLeapYear(years):
    '''
    通过判断闰年，获取年份years下一年的总天数
    :param years: 年份，int
    :return:days_sum，一年的总天数
    '''
    # 断言：年份不为整数时，抛出异常。
    assert isinstance(years, int), "请输入整数年，如 2018"

    if ((years % 4 == 0 and years % 100 != 0) or (years % 400 == 0)):  # 判断是否是闰年
        # print(years, "是闰年")
        days_sum = 366
        return days_sum
    else:
        # print(years, '不是闰年')
        days_sum = 365
        return days_sum


def getAllDayPerYear(start_date, end_date):
    """
    获取所有日期

    """
    r = getTradeDates(start_date, end_date)
    all_date_list = []
    years = sorted(set([i[:4] for i in r]))
    for year in years:
        start_date = '%s-1-1' % year
        a = 0
        days_sum = isLeapYear(int(year))
        while a < days_sum:
            b = arrow.get(start_date).shift(days=a).format("YYYYMMDD")
            a += 1
            all_date_list.append(b)
    return all_date_list


def CheckDate(date):
    """
    判断日期是否是第三周周四
    """
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:8])
    end = int(datetime.datetime(year, month, day).strftime("%W"))  # 当天的周数
    begin = int(datetime.datetime(year, month, 1).strftime("%W"))  # 此月1号的周数
    if datetime.datetime(year, month, 1).weekday() < 5:
        if end - begin + 1 == 3:  # 判断日期是否是第三周周四
            week = datetime.datetime.strptime(date, '%Y%m%d').weekday()
            if int(week) == 3:
                return getTradeSectionDates(date, -1)[0]
            else:
                return None
        else:
            return None
    else:
        if end - begin + 1 == 4:  # 判断日期是否是第三周周四
            week = datetime.datetime.strptime(date, '%Y%m%d').weekday()
            if int(week) == 3:
                return getTradeSectionDates(date, -1)[0]
            else:
                return None
        else:
            return None


def getDateList(start_date='20100101', end_date=(str(datetime.datetime.now().year))+'1231'):
    """
    周四list
    """
    res_list = []
    date_list = getAllDayPerYear(start_date, end_date)
    for date in date_list:
        res = CheckDate(date)
        if res != None:
            res = getTradeSectionDates(res, 1)[0]
            res_list.append(res)
    redis_cli.set('ContractDate', str(res_list))
    return res_list


def getRedisContractDate(date):
    data = redis_cli.get('ContractDate')
    if data:
        res = eval(data)
        if res[-1] < date:
            return getDateList(end_date=date[:4]+'1231')
        elif res[0] > date:
            return getDateList(start_date=date[:4]+'0101')
        else:
            return res
    else:
        return getDateList()

def get_main_contract(trade_date, maincode):
    db = Database(WIND_DB)
    sql = "select FS_MAPPING_WINDCODE, S_INFO_WINDCODE, STARTDATE, ENDDATE from wind.CfuturesContractMapping where " \
          " STARTDATE <= {} and ENDDATE >= {} and S_INFO_WINDCODE = '{}' ".format(trade_date, trade_date, maincode)

    db.cursor.execute(sql)
    data = db.cursor.fetchall()
    df = pd.DataFrame(data, columns=['FS_MAPPING_WINDCODE', 'S_INFO_WINDCODE', 'STARTDATE', 'ENDDATE'])
    return df.FS_MAPPING_WINDCODE.values[0]





def getContract(trade_date, contract_type, dely_date, season_con=False):
    """
    每月第三个周五换合约
    """
    date_ahead = getTradeSectionDates(trade_date, dely_date + 1)[-1]  # 提前n天换合约的日期
    # print(date)
    # print(date_ahead)
    res_list = getRedisContractDate(trade_date)  # 每月周四日期list(每个合约开始日期)
    mid_list = res_list.copy()
    mid_list.append(trade_date)
    mid_list.append(date_ahead)
    mid_list = sorted(set(mid_list))
    date_index = mid_list.index(trade_date)
    date_ahead_index = mid_list.index(date_ahead)
    contract_prefix, contract_suffix = contract_type.split('.')
    if date_ahead_index - date_index == 0 and trade_date not in res_list:
        contract_mid = mid_list[date_index + 1][2:6]
    elif date_ahead_index - date_index == 1 and date_ahead in res_list:
        contract_mid = mid_list[date_ahead_index][2:6]
    elif dely_date == 0 and trade_date in res_list:
        contract_mid = mid_list[date_index][2:6]
    else:
        contract_mid = mid_list[(date_ahead_index + 1)][2:6]
    if season_con:
        month = contract_mid[-2:]
        month = int(month) + 1

        if (month//3 + 1) * 3 <= 12:
            new_month = (month // 3 + 1) * 3
        else:
            new_month = (month//3 + 1) * 3 - 12
            contract_mid = str(int(contract_mid[:2])+1) + contract_mid[-2:]
        new_con_appix = str(new_month).zfill(2)
        contract_mid = contract_mid[:2] + new_con_appix
    contract_res = contract_prefix + contract_mid + '.' + contract_suffix

    return contract_res


    # if dely_date == 0:
    #     return get_main_contract(trade_date, contract_type)
    # else:
    #     date_ahead = getTradeSectionDates(trade_date, dely_date+1)[-1]  # 提前n天换合约的日期
    #     # print(date)
    #     # print(date_ahead)
    #     res_list = getRedisContractDate(trade_date)  # 每月周四日期list(每个合约开始日期)
    #     mid_list = res_list.copy()
    #     mid_list.append(trade_date)
    #     mid_list.append(date_ahead)
    #     mid_list = sorted(set(mid_list))
    #     date_index = mid_list.index(trade_date)
    #     date_ahead_index = mid_list.index(date_ahead)
    #     contract_prefix, contract_suffix = contract_type.split('.')
    #     if date_ahead_index-date_index == 0 and trade_date not in res_list:
    #         contract_mid = mid_list[date_index+1][2:6]
    #     elif date_ahead_index-date_index == 1 and date_ahead in res_list:
    #         contract_mid = mid_list[date_ahead_index][2:6]
    #     elif dely_date == 0 and trade_date in res_list:
    #         contract_mid = mid_list[date_index][2:6]
    #     else:
    #         contract_mid = mid_list[(date_ahead_index + 1)][2:6]
    #     contract_res = contract_prefix + contract_mid + '.' + contract_suffix
    #     return contract_res


if __name__ == '__main__':
    # all_date_list = getAllDayPerYear('20150101', '20161231')
    # getDateList('20100101', '20211231')
    # a = get_main_contract('20100517', 'IF.CFE')
    a = getContract('20150222', 'IF.CFE', 0, season_con=True)

    print(a)
















