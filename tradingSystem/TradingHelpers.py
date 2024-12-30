#-*- coding:utf-8 -*-
import numpy as np
import pandas as pd
np.set_printoptions(suppress=True)

def _where_windcodes(where):
    windcode = None
    if isinstance(where, dict):
        windcode = where.get("windcode")
    return windcode

def BuildPositionsDF(positions_list, account_titles, where):
    """
    :param positions_list: list
        [[账户(多级)], 万得代码, 市场类型, 证券代码, 证券名称, 持仓数量, 持仓金额, 持仓成本,多空方向]
    :param account_titles: list
        账户各级的列名
    :param where: dict
        过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["WIND_CODE", "MARKET_TYPE", "SECURITY_CODE", "SECURITY_NAME", "POSITION", "NOTIONAL", "COST", "LS"]]
    """
    # 下面把List转换为Pandas.DataFrame对象
    if (not positions_list):
        positions_list.append([list(account_titles), 'NONE', 'NONE', 'NONE' ,'NONE', 0, 0.0, 0.0,1])
    np_position = np.array(positions_list,dtype=object)

    wind_code = np_position[:, 1]
    df = pd.DataFrame(np_position[:, 5:],
                      columns=["POSITION", "NOTIONAL", "COST","LS"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_position[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_position[:, 1]
    df["MARKET_TYPE"] = np_position[:, 2]
    df["SECURITY_CODE"] = np_position[:, 3]
    #df["BS_FLAG"] = np_position[:, 4]
    df["SECURITY_NAME"] = np_position[:, 4]

    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    df = df.sort_index(ascending=True)

    # 规整列
    # 万的代码， 市场类型， 证券代码， 证券名称， 持仓数量， 持仓金额， 成本价格
    df = df[account_titles + ["WIND_CODE", "MARKET_TYPE", "SECURITY_CODE", "SECURITY_NAME", "POSITION", "NOTIONAL", "COST","LS"]]
    #df.index.name = 'WIND_CODE'
    df = df[df.WIND_CODE != 'NONE']

    return df

def BuildTradesDF(trades_list, account_titles,  where):
    '''
    :param trades_list: [[账户(多级)], 万得代码, 证券名称, 交易类型， 证券代码, 市场类型, VOLUME, AMOUNT]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles+["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", "TRADE_TYPE", "SECURITY_NAME", "TRADE_PRICE", "TRADE_VOLUME", "TRADE_AMOUNT"]]
    '''
    if (not trades_list):
        trades_list.append([list(account_titles), 'NONE', 'NONE', 'NONE', 'NONE', 'NONE', 0, 0.0])

    np_trades = np.array(trades_list)
    key = np_trades[:, 1]
    df = pd.DataFrame(np_trades[:, 6:],
                      columns=["TRADE_VOLUME", "TRADE_AMOUNT"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_trades[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_trades[:, 1]
    df["SECURITY_NAME"] = np_trades[:, 2]
    df["TRADE_TYPE"] = np_trades[:, 3]
    df["SECURITY_CODE"] = np_trades[:, 4]
    df["MARKET_TYPE"] = np_trades[:, 5]
    df["TRADE_PRICE"] = df["TRADE_AMOUNT"] / df["TRADE_VOLUME"].round(decimals=4)

    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    # 规整列
    df = df[account_titles+
        ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", "SECURITY_NAME", "TRADE_TYPE", "TRADE_PRICE", "TRADE_VOLUME", "TRADE_AMOUNT"]]
    df = df[df.SECURITY_CODE != 'NONE']

    return df


def BuildOrdersDF(order_list, account_titles, where):
    '''
    :param order_list: [[账户(多级)], 万得代码, 交易类型, 证券代码, 市场类型, VOLUME]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME"]]
    '''
    if (not order_list):
        order_list.append([list(account_titles), 'NONE', 'NONE', 'NONE', 'NONE', 0])
    np_orders = np.array(order_list)
    df = pd.DataFrame(np_orders[:, 5],
                      columns=["ORDER_VOLUME"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_orders[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_orders[:, 1]
    df["TRADE_TYPE"] = np_orders[:, 2]
    df["SECURITY_CODE"] = np_orders[:, 3]
    df["MARKET_TYPE"] = np_orders[:, 4]

    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    #规整列
    df = df[account_titles + ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME"]]
    df = df[df.SECURITY_CODE != 'NONE']

    return df

def BuildOriginalOrdersDF(original_order_list, account_titles, where):
    '''
    :param original_order_list: [[账户(多级)], 万得代码, 交易类型, 证券代码, 市场类型, 委托量, 已成交量, 委托金额, 是否可撤(Y/N/F), 撤销状态(F/T),撤销KEY,委托时间,委托状态]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE", "CANCEL_KEY"]]
    '''
    if (not original_order_list):
        original_order_list.append([list(account_titles), 'windcode', 'B/S', 'security_code', 'mkt_type', 0, 0, 0.0, "Y/N/F", "cancel_key",'',''])
    np_orders = np.array(original_order_list)
    df = pd.DataFrame(np_orders[:, 5:8],
                      columns=["ORDER_VOLUME", "FILLED_VOLUME", "ORDER_PRICE"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_orders[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_orders[:, 1]
    df["TRADE_TYPE"] = np_orders[:, 2]
    df["SECURITY_CODE"] = np_orders[:, 3]
    df["MARKET_TYPE"] = np_orders[:, 4]
    df["CANCELABLE"] = np_orders[:, 8]
    df["CANCEL_KEY"] = np_orders[:, 9]
    df['INSTR_TIME'] = np_orders[:,10]
    df['ORDER_STATE'] = np_orders[:,11]




    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    # df = df[df['WIND_CODE'].isin(filter_windcode)]

    #规整列
    df = df[account_titles + ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE", "CANCEL_KEY","INSTR_TIME","ORDER_STATE"]]
    df = df[df.SECURITY_CODE != 'security_code']

    return df


def BuildOriginalOrdersDF_New(original_order_list, account_titles, where):
    '''
    :param original_order_list: [[账户(多级)], 万得代码, 交易类型, 证券代码, 市场类型, 委托量, 已成交量, 委托金额, 是否可撤(Y/N/F), 撤销状态(F/T),撤销KEY]
    :param account_titles: 账户各级的列名
    :param where: 过滤条件。如果是dict类型并且存在key为windcode, 则结果集根据windcode过滤
    :return: pandas.DataFrame
        columns=[account_titles + ["SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE", "CANCEL_KEY","remark"]]
    '''
    if (not original_order_list):
        original_order_list.append([list(account_titles), 'windcode', 'B/S', 'security_code', 'mkt_type', 0, 0, 0.0, "Y/N/F", "F/T","cancel_key","remark"])
    np_orders = np.array(original_order_list)
    df = pd.DataFrame(np_orders[:, 5:8],
                      columns=["ORDER_VOLUME", "FILLED_VOLUME", "ORDER_PRICE"],
                      dtype=float)
    # 拆ACCOUNT
    acct_array = np.array(np_orders[:, 0].tolist())
    for i in range(0, len(account_titles)):
        df[account_titles[i]] = acct_array[:, i]

    df["WIND_CODE"] = np_orders[:, 1]
    df["TRADE_TYPE"] = np_orders[:, 2]
    df["SECURITY_CODE"] = np_orders[:, 3]
    df["MARKET_TYPE"] = np_orders[:, 4]
    df["CANCELABLE"] = np_orders[:, 8]
    df['CANCEL_FLAG'] = np_orders[:,9]
    df["CANCEL_KEY"] = np_orders[:, 10]
    df["REMARK"] = np_orders[:, 11]


    # 按照where中的万得代码过滤
    filter_windcode = _where_windcodes(where)
    if filter_windcode:
        condition = df["WIND_CODE"] == ""
        for windcode in filter_windcode:
            condition |= df["WIND_CODE"] == windcode
        df = df[condition]

    # df = df[df['WIND_CODE'].isin(filter_windcode)]

    #规整列
    df = df[account_titles + ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", 'TRADE_TYPE', "ORDER_VOLUME", "FILLED_VOLUME",
                              "ORDER_PRICE", "CANCELABLE","CANCEL_FLAG", "CANCEL_KEY","REMARK"]]
    df = df[df.SECURITY_CODE != 'security_code']

    return df
