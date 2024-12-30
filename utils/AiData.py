import time
import _pickle
import traceback
from collections import defaultdict
from datetime import datetime

import pandas as pd
from utils.Date import *
from utils import daily_data,eod_data
from configs.Database import *
from concurrent.futures import ThreadPoolExecutor


def getATotalStop(startDay=None, endDay=None):
    """
    找到所有涉及的A股的停牌情况
    :param startDay: 2019-01-01
    :param endDay: 2019-01-01
    :return:
    """
    # start = time.strftime('%Y%m%d', time.strptime(startDay, '%Y-%m-%d'))
    # end = time.strftime('%Y%m%d', time.strptime(endDay, '%Y-%m-%d'))
    sql = """select s_info_windcode, s_dq_suspenddate from wind.ASharetradingsuspension where s_dq_suspenddate >= '{}' 
and s_dq_suspenddate <= '{}'""".format(startDay, endDay)
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df_stop = pd.DataFrame(data=data, columns=['s_info_windcode', 's_dq_suspenddate'])
    return df_stop


def getATotalST(time_data):
    """
    找到所有涉及的A股的ST情况
    :param time_data: 2019-01-01
    :return: DF
    """
    # start = time.strftime('%Y%m%d', time.strptime(time_data, '%Y-%m-%d'))
    sql = """select S_INFO_WINDCODE, entry_dt, remove_dt from wind.AShareST where remove_dt >= '{}' or remove_dt is NULL
""".format(time_data)
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df_st = pd.DataFrame(data=data, columns=['code', 'entry', 'remove'])
    return df_st


def getFuturesContractMultiplierDB(market_quotes, start_day, end_day, condition="CFE"):
    '''
    合约乘数
    :param start_day: 策略起始日期
    :param end_day: 策略结束日期
    :param condition: 合约后缀筛选条件
    :return:
    '''
    data = market_quotes['CFuturesContPro'].copy()
    future = market_quotes['CFuturesDescription'].copy()
    future = future[(future['S_INFO_LISTDATE'] < end_day) & (future['FS_INFO_LTDLDATE'] > start_day)][
        'S_INFO_WINDCODE'].values.tolist()
    data = data[(data['S_INFO_WINDCODE'].str.contains(condition)) & (data['S_INFO_WINDCODE'].isin(future))]
    data.fillna(1, inplace=True)
    data['MUL'] = data['S_INFO_PUNIT'] * data['S_INFO_CEMULTIPLIER'] * data['S_INFO_RTD']
    result = data[['S_INFO_WINDCODE', 'MUL']].set_index('S_INFO_WINDCODE').to_dict()
    return result


def getMarginRate(market_quotes, start_day, end_day, condition='CFE'):
    '''
    保证金
    :param start_day: 策略起始日期
    :param end_day: 策略结束日期
    :param condition: 合约后缀筛选条件
    :return:
    '''
    data = market_quotes['CFuturesmarginratio'].copy()
    data['MARGINRATIO'] = data['MARGINRATIO'].astype('float') / 100
    future = market_quotes['CFuturesDescription'].copy()
    future = future[(future['S_INFO_LISTDATE'] < end_day) & (future['FS_INFO_LTDLDATE'] > start_day)][
        'S_INFO_WINDCODE'].values.tolist()
    data = data[(data['S_INFO_WINDCODE'].str.contains(condition)) & (data['S_INFO_WINDCODE'].isin(future))]
    data = data.rename(columns={'S_INFO_WINDCODE': 'windcode', 'TRADE_DT': 'trade_date', 'MARGINRATIO': 'margin_ratio'})
    data.set_index('windcode', inplace=True)
    data.sort_values(by='trade_date', inplace=True)
    return data


def getMarketDataSingle(table, year, code):
    try:
        with open('/share_data/Wind_Data/{}/{}/{}.pkl'.format(table, year, code), 'rb') as f:
            df = _pickle.load(f)
    except Exception as e:
        df = pd.DataFrame()
    return df


def getWindData(table, code_list=[], start_date='20150105', end_date='20200902', fields=[], multi=pd.DataFrame()):
    """
    获取pickle数据
    :param table: 表名
    :param code_list: 所需wind代码
    :param start_date: 起始时间
    :param end_date: 结束时间
    :param fields: 所需字段，不传取所有
    :return:
    """
    date_field = getDateField(table)
    if table in daily_data:
        market_date = getTradeDates(start_date, end_date)
        years = sorted(set([i[:4] for i in market_date]))
        res = []
        columns = []
        # 根据 年份/标的 拿到pickle数据
        for year in years:
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(getMarketDataSingle, table, year, code) for code in
                         code_list]
            for t in tasks:
                df = t.result()
                if not df.empty:
                    columns = df.columns.tolist()
                res.extend(df.values.tolist())
        if not res:
            df_res = pd.DataFrame(columns=fields)
        else:
            dd = pd.DataFrame(res, columns=columns)
            df_res = getFieldsRes(fields, table, dd, date_field, multi=multi)
            df_res = df_res.sort_values(by=['S_INFO_WINDCODE', date_field]).reset_index(drop=True)
            df_res = df_res[(df_res[date_field] >= start_date) & (df_res[date_field] <= end_date)].reset_index(drop=True)
        if df_res.empty:
            print('未取到数据{}表,起始时间{},结束时间{}'.format(table, start_date, end_date))



    else:
        try:
            with open('/share_data/Wind_Data/{}/{}.pkl'.format(table, table), 'rb') as f:
                dd = _pickle.load(f)
        except Exception as e:
            dd = pd.DataFrame()
            print(e)
        df_res = getFieldsRes(fields, table, dd, date_field, multi=pd.DataFrame())
        df_res = df_res
    return df_res


def getFieldsRes(fields, table, dd, date_field, multi=pd.DataFrame()):
    if fields:
        if 'AVERAGE' in fields:
            if table in ['AIndexEODPrices', 'AShareEODPrices', 'ChinaClosedFundEODPrice']:
                dd['AVERAGE'] = dd['S_DQ_AMOUNT'] / dd['S_DQ_VOLUME'] * 10
            elif table in ['HKIndexEODPrices', 'HKshareEODPrices']:
                dd['AVERAGE'] = dd['S_DQ_AMOUNT'] / dd['S_DQ_VOLUME'] * 1000
            else:
                dd['MUL'] = dd['S_INFO_WINDCODE'].map(lambda x:multi[x])
                dd['AVERAGE'] = dd['S_DQ_AMOUNT'] / dd['S_DQ_VOLUME'] / dd['MUL'] * 10000
        fields = [i for i in fields if i in dd.columns.tolist()]
        if table in daily_data:
            res_fields = ['S_INFO_WINDCODE', date_field]
            for i in fields:
                if i not in res_fields:
                    res_fields.append(i)
            df_res = dd[res_fields]
        else:
            df_res = dd[fields]

    else:
        df_res = dd
    return df_res


def getDateField(table):
    if table == 'AShareTradingSuspension':
        date_field = 'S_DQ_SUSPENDDATE'
    elif table == 'AShareConsensusRollingData':
        date_field = 'EST_DT'
    elif table == 'AShareStockRatingConsus':
        date_field = 'RATING_DT'
    else:
        date_field = 'TRADE_DT'
    return date_field


def getPERatio(start_time, end_time, wind_code=[], fields=[]):
    """
    Describe: 传递万得代码返回对应市盈率等
    :param wind_code:万得代码
    :param start_time: 开始日期
    :param end_time: 结束日期
    :param fields: 返回字段
    :return: 行业(中文)
    """
    start_time = time.strftime('%Y%m%d', time.strptime(start_time, '%Y-%m-%d'))
    end_time = time.strftime('%Y%m%d', time.strptime(end_time, '%Y-%m-%d'))
    aiwind_oracle = Database(WIND_DB)

    if len(wind_code) > 1:
        conditions = "S_INFO_WINDCODE in {}".format(tuple(wind_code))
    else:
        conditions = "S_INFO_WINDCODE = '{}'".format(wind_code[0])
    table_name = "AShareEODDerivativeIndicator"
    sql = queryWindDB(table_name, start_time, end_time, fields, conditions)
    aiwind_oracle.cursor.execute(sql)
    industriesData = aiwind_oracle.cursor.fetchall()
    if not fields:
        sql1 = "select COLUMN_NAME from all_tab_columns where table_name =upper('{}')".format(table_name)
        aiwind_oracle.cursor.execute(sql1)
        fields = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df = pd.DataFrame(data=industriesData, columns=fields)
    return df


def queryWindDB(table_name=None, start_time=None, end_time=None, fields=None, conditions=None):
    """日行情数据库查询接口"""

    if fields == None or fields == []:
        fields = ['*']

    if conditions:
        conditions = '{} AND '.format(conditions)
    conditions = " {} TRADE_DT >= '{}' AND   TRADE_DT <= '{}' ".format(conditions, start_time, end_time)

    sql = getSelectSql(table_name, fields, conditions)

    # aiwind_oracle = OracleEngine(db_config.aiwind_oracle_db)
    # data = aiwind_oracle.getFetchAll(sql)
    # aiwind_oracle.close()
    return sql


# 基本查寻SQL语句拼接
def getSelectSql(table, fields=None, conditions=None, isDistinct=None, order=None):
    '''
        生成select的sql语句
    @table，查询记录的表名
    @key，需要查询的字段
    @conditions,插入的数据，字典
    @isDistinct,查询的数据是否不重复
    '''
    if isDistinct:
        sql = 'select distinct %s ' % ",".join(fields)
    elif fields == None or fields == []:
        sql = 'select  * '
    else:
        sql = 'select  %s ' % ",".join(fields)

    sql += ' from %s ' % table
    if conditions:
        sql += ' where %s ' % conditions
    if order:
        sql += order
    # print(sql)
    return sql


def which_table(wind_code=None):
    """判断股票类型"""
    if wind_code is None:
        return None
    if "." not in wind_code:
        return None
    # 获取后缀
    mkt_code = wind_code.split('.', 1)[1]
    # 获取前缀
    code_prefix = wind_code[0:2]
    # 获取数字长度
    code_len = len(wind_code.split('.', 1)[0])
    # 根据windcode调用API
    if mkt_code in ['SH', 'SZ']:
        if code_prefix in ['60', 'T0', '00', '30', '68']:
            if code_prefix == '00' and mkt_code == 'SH':
                return 'AIndexEODPrices'
            else:
                return 'AShareEODPrices'
        elif code_prefix in ['50', '51', '15', '16', '18']:
            return 'ChinaClosedFundEODPrice'
        elif code_prefix in ['90', '92', '10', '20', '11']:
            return 'ChinaOptionEODPrices'
        else:
            return 'AIndexEODPrices'
    elif mkt_code == 'CSI':
        return 'AIndexEODPrices'
    elif mkt_code == 'HI':
        return 'HKIndexEODPrices'
    elif mkt_code in ['HK', 'HKS']:
        if code_prefix == 'RX':
            return 'HKIndexEODPrices'
        else:
            return 'HKshareEODPrices'
    elif mkt_code == 'CFE':
        if code_len >= 10:
            return 'ChinaOptionEODPrices'
        elif code_prefix[0] == 'T':
            return 'CBondFuturesEODPrices'
        else:
            return 'CIndexFuturesEODPrices'
    else:
        if code_len >= 10:
            return 'ChinaOptionEODPrices'
        else:
            return 'CCommodityFuturesEODPrices'


def loadCommissionRate(strategy_ids, env='dev'):
    '''
    从commission_rate表获取佣金率
    :param strategy_ids: 只能传资管策略list
    :return:
    '''
    result = defaultdict(dict)
    strategy_id = str(strategy_ids).replace('[', '').replace(']', '')
    if not strategy_id:
        return result
    with mysql(env) as cursor:
        sql = "select strategy_id, windcode, commission from commission_rate where strategy_id in ({})".format(strategy_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        sql = "select windcode, commission from commission_rate where strategy_id ='default'"
        cursor.execute(sql)
        data_default = cursor.fetchall()
    # 初始化默认参数
    for id in strategy_ids:
        result[id] = {i[0]: i[1] for i in data_default}
    # 覆盖参数
    for res in data:
        result[res[0]][res[1]] = res[2]
    return result

def fill_account_type(row: pd.Series):
    '''
    判断期货、现货
    :param row:
    :return:
    '''
    if row.empty:
        return 'CASH'
    if row['windcode'].endswith(('CFE', 'CZC', 'SHF', 'DCE')):
        return 'FUTURE'
    else:
        return 'CASH'

def getCommission(row:pd.Series, commission={}):
    '''
    根据策略和windcode获取佣金率
    :param commissionRate: dict, loadCommissionRate函数返回值
    :param row: pd.Series()
    :return:
    '''
    res = 0
    if row.empty: return res
    commission = commission.get(row['strategy_id'], {})
    if row['windcode'] in commission:
        res = commission[row['windcode']]
    else:
        for key in commission:
            if row['windcode'].split('.')[1] == key.split('.')[1]:
                res = commission[key]
                break
    return res


def loadFeeRate(total_security_list, strategy_configs):
    """
    加载费率信息
    :param total_security_list:
    :param strategy_configs:
    :return:
    """
    business_types = set([config['business_type'] for config in strategy_configs])
    sql = "select business_type,windcode,fee_type,fee_rate from trading_fee_rate where business_type"
    if len(business_types) > 1:
        sql = sql + " in {0}".format(tuple(business_types))
    elif len(business_types) == 1:
        sql = sql + " = '{0}'".format(business_types.pop())
    else:
        exit("Error: No Business Type")
    with mysql(SHARE) as cursor:
        cursor.execute(sql)
        data = cursor.fetchall()
    df = pd.DataFrame(data,columns=['business_type','windcode','fee_type','fee_rate'])
    df['fee_rate'] = df['fee_rate'].astype('float')
    df['BS'] = df['fee_type'].map({'B':1,'S':-1,'OPEN':1,'CLOSE':-1})
    return df


def getFutureData(env, strategy_ids:list):
    '''
    获取策略主力合约\映射合约\合约乘数
    返回主力合约字典以及主力合约映射合约df
    '''
    strategy_id = str(strategy_ids).replace('[', '').replace(']', '')
    with mysql(env) as cursor:
        cursor.execute("SELECT a.strategy_id, b.value FROM strategy_config a, risk_config b WHERE a.strategy_id IN ({}) "
                       "AND a.risk_id = b.risk_id AND b.key LIKE 'hedge%'".format(strategy_id))
        maincode = {i[0]: i[1] for i in cursor.fetchall()}
    sql = "select S_INFO_WINDCODE,STARTDATE,ENDDATE,FS_MAPPING_WINDCODE from CFUTURESCONTRACTMAPPING " \
          "where S_INFO_WINDCODE in ({})".format(str(list(maincode.values())).replace('[','').replace(']',''))
    df = pd.read_sql(sql=sql, con=Database(WIND_DB).conn)
    with oracle(cursor_type='dict') as cursor:
        code = str(list(set([i.split('.')[0] for i in maincode.values()]))).replace('[','').replace(']','')
        cursor.execute("select S_INFO_WINDCODE as code, nvl(S_INFO_PUNIT,1)*nvl(s_info_cemultiplier,1)*nvl(s_info_rtd,1) "
                       "as multi from CFUTURESCONTPRO where S_INFO_CODE in ({})".format(code))
        multi = {i[0]: i[1] for i in cursor.fetchall()}
    return maincode, df, multi


def getPreDayDict(start_date, end_date):
    '''
    获取日期序列的前一交易日
    :param start_date:
    :param end_date:
    :return:
    '''
    date_list = getTradeDates(start_date=start_date, end_date=end_date)
    tmp = pd.DataFrame(zip(date_list, date_list), columns=['trade_date', 'pre_day'])
    tmp['pre_day'] = tmp['pre_day'].shift(1)
    date_dict = tmp.set_index('trade_date')['pre_day'].to_dict()
    return date_dict

def getFutureCode(row, mapdata):
    """
    获取主力合约指定日期对应的合约代码
    """
    mapdata = mapdata[(mapdata['S_INFO_WINDCODE'] == row['maincode']) &
                      (mapdata['STARTDATE'] <= row['trade_date']) &
                      (mapdata['ENDDATE'] >= row['trade_date'])]
    futurecode = mapdata['FS_MAPPING_WINDCODE'].values[0]
    return futurecode

def getPriceData(code_list=[], start_date='20150105', end_date='20200902', fields=[]):
    windInfoDict = defaultdict(lambda: defaultdict(set))
    for stock in code_list:
        table = which_table(stock)
        windInfoDict[table]['codes'].add(stock)
    res = pd.DataFrame()
    for table, info in windInfoDict.items():
        res = res.append(getWindData(table, info['codes'], start_date, end_date, fields))
    if end_date == datetime.now().strftime('%Y%m%d') :
        res = addProdPrice(res, end_date, code_list)
    return res

def addProdPrice(res, end_date, code_list):
    '''
    生产拼接行情
    :param res:
    :param end_date:
    :param code_list:
    :return:
    '''
    if end_date not in set(res['TRADE_DT'].values.tolist()):
        code = str(code_list).replace('[', '').replace(']', '')
        with mysql('prod') as cursor:
            cursor.execute("select windcode, trade_date, pre_close, `close`,pctchange from ai_stock_price "
                           "where trade_date = '{}' and windcode in ({})".format(end_date, code))
            marketData = pd.DataFrame(list(cursor.fetchall()), columns=['S_INFO_WINDCODE','TRADE_DT', 'S_DQ_PRECLOSE',
                                                                        'S_DQ_CLOSE','S_DQ_PCTCHANGE'])
        marketData['TRADE_DT'] = marketData['TRADE_DT'].map(lambda x: str(x).replace('-', ''))
        # if marketData.empty:
        #     raise Exception('无今日行情')
        columns = set(res.columns) & set(marketData.columns)
        res = res.append(marketData[list(columns)])
    return res


def getHKTotalStop(startDay=None, endDay=None):
    """
    找到所有涉及的港股的停牌情况
    """
    sql = "select s_info_windcode, suspenddate from wind.HKTransactionStatus where suspenddate>='{}'and " \
          "suspenddate<='{}'".format(startDay, endDay)
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df_stop = pd.DataFrame(data=data, columns=['s_info_windcode', 's_dq_suspenddate'])
    return df_stop


def getHKTotalEnd():
    """
    港股退市
    """
    sql = "select s_info_windcode, s_delistdt from wind.HKShareEndlist"
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df_end = pd.DataFrame(data=data, columns=['s_info_windcode', 's_delistdt'])
    return df_end


def getHKCodes():
    """
    万得港股通100
    """
    sql = "select a.F_INFO_WINDCODE, a.S_CON_WINDCODE, b.S_INFO_NAME from wind.AIndexMembersWIND a " \
          "join wind.hksharedescription b on a.S_CON_WINDCODE = b.S_INFO_WINDCODE where a.F_INFO_WINDCODE = 'GGT100.WI' " \
          "and a.cur_sign = '1'"
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df = pd.DataFrame(data=data, columns=['F_INFO_WINDCODE', 'S_CON_WINDCODE', 'S_INFO_NAME'])
    df['WINAME'] = '万得港股通100'
    df = df[['F_INFO_WINDCODE', 'WINAME', 'S_CON_WINDCODE', 'S_INFO_NAME']]
    return df


class SecurityBlackList(object):

    def getReplacementList(self, wind_code):
        """
        Describe :禁买wind_code替换函数
        :param wind_code:万得代码
        :return:替换后的万得代码
        """

        data = getReplaceListDB(wind_code)
        replacementList = set()
        for security in data:
            replacementList.add(security[0])
        buyBlackList = set(self.getBlackList(tradetype='buy')['wind_code'].values)
        results = replacementList - buyBlackList
        results_list = list(results)

        return results_list

    def getBlackList(self, tradetype, wind_code=None, replace=None):
        """
        Describe :通过参数查询禁买卖池数据
        :param tradetype: 交易类型 buy,sell
        :param wind_code: 万得代码
        :param replace: 是否返回替换万德代码,参数'Y'
        :return: 对应查询数据
        """
        if wind_code is not None:
            blackList = getBlackListDB(wind_code)
            if blackList is None:
                return True
            # able to buy or sell when the return is True
            if tradetype == 'buy':
                if blackList[2] != 'N':
                    return True
                else:
                    if replace == "Y":
                        replace_list = self.getReplacementList(wind_code)
                        return False, replace_list
                    else:
                        return False
            elif tradetype == 'sell':
                return blackList[3] != 'N'
            else:
                print('wrong tradetype')
                return None
        # 查询禁买卖池所有数据
        else:
            blackList = getBuyAndSellListDB(tradetype)
            if blackList is None:
                return None
            else:
                df_data = []
                for i in blackList:
                    df_data.append(i)
                df = pd.DataFrame(df_data, columns=['wind_code'])
                return df


def getBuyAndSellListDB(tradetype=None):
    """查询特定交易类型下的全部数据"""

    if tradetype == 'buy':
        sql = "SELECT windcode FROM ai_share.restrict_security_list WHERE able2buy='N'"
    elif tradetype == 'sell':
        sql = "SELECT windcode FROM ai_share.restrict_security_list WHERE able2sell='N'"
    else:
        print('wrong tradetype')
        return None
    aidb_oracle = Database(AI_SHARE)
    aidb_oracle.cursor.execute(sql)
    data = aidb_oracle.cursor.fetchall()
    aidb_oracle.close()
    return data


# 查询禁买卖池指定标的是否存在,参数wind_code, 返回一条数据(元组)
def getBlackListDB(wind_code=None):
    """ 查询禁买卖池"""

    table = 'ai_share.restrictseculist'
    fields = ['*']
    conditions = "windcode='{}'".format(wind_code)
    sql = getSelectSql(table, fields, conditions)
    aidb_oracle = Database(AI_SHARE)
    aidb_oracle.cursor.execute(sql)
    data = aidb_oracle.cursor.fetchone()
    aidb_oracle.close()
    return data


# 查询备用万得代码,返回值元组类型
def getReplaceListDB(wind_code=None):
    """查询代替windcode"""
    table = 'REPLACE_SECURITY_LIST'.lower()
    fields = ['backup_security']
    conditions = "windcode='{}'  order by priority".format(wind_code)
    sql = getSelectSql(table, fields, conditions)
    aiwind_oracle = Database(AI_SHARE)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    return data


# 查询标的最小价格变动单位

def getMinPriceCHG_UNIT(windcode=''):
    """
    查询标的最小价格变动单位
    """
    sql = "select S_INFO_MIN_PRICE_CHG_UNIT FROM WINDCUSTOMCODE WHERE S_INFO_WINDCODE = '{}'".format(windcode)
    aiwind_oracle = Database(WIND_DB)
    try:
        aiwind_oracle.cursor.execute(sql)
        data = aiwind_oracle.cursor.fetchall()
        return data[0][0]
    except:
        print('got price_chg_unit error:{}'.format(traceback.format_exc()))
        return 0.01
    finally:
        aiwind_oracle.close()

def getAShareCalendar(start_date='20150101', end_date='20210501'):
    """
        中国A股交易日历
    """
    # start = time.strftime('%Y%m%d', time.strptime(time_data, '%Y-%m-%d'))
    sql = """select TRADE_DAYS, S_INFO_EXCHMARKET from wind.AShareCalendar where S_INFO_EXCHMARKET = 'SSE' \
    and TRADE_DAYS >= '{}' and  TRADE_DAYS <= '{}' """.format(start_date, end_date)
    aiwind_oracle = Database(WIND_DB)
    aiwind_oracle.cursor.execute(sql)
    data = aiwind_oracle.cursor.fetchall()
    aiwind_oracle.close()
    df_tradedt = pd.DataFrame(data=data, columns=['date', 'S_INFO_EXCHMARKET'])
    # 调取每周第一个交易日
    df_tradedt['date'] = pd.to_datetime(df_tradedt['date'])
    df_tradedt1 = df_tradedt.set_index('date').resample('W')['S_INFO_EXCHMARKET'].first()
    lis = df_tradedt1.index.astype(str).tolist()
    print(df_tradedt)
    print(df_tradedt1)

    return [x[:4]+x[5:7]+x[8:10] for x in lis]



if __name__ == '__main__':
    print(getAShareCalendar('20150101','20150601'))
    # print(which_table('IF2102.CFE'))