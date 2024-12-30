#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:innerconfig.py
@time:2020/05/19
"""

MQ_SERVER_IP = {'test': "10.27.116.135",
                # 'prod': '172.27.14.164' # sz
                'prod': '172.23.7.143'  # BJ-jj
                }
mqBasePort = {
    'test': 45678,
    'prod': 45678
}

# CATS_ACCT = "701896"
# CATS_PWD = "111111"
# LOCAL_IP = '10.24.206.196'
# macAddr = '44:39:c4:50:f4:39'
hdSerial = 'WD-WCC2E6HJUP9C'

# TRADE_ACCT = "30100199407"
# TRADE_ACCTTYPE = "S0"
# TRADE_PWD = "123456"


tradeSideToStr = {
    '1': 'BUY',
    '2': 'SELL'
}

futureEnds = ('CFE',)

windMarket2catsMarket = {
    'CFE': 'CFFEX'
}

futureTradeSide = {
    '1^1': 'FA',  # 开仓买入(开多仓)
    '1^-1': 'FB',  # 开仓卖出(开空仓)
    '2^-1': 'FC',  # 平仓买入(平空仓)
    '2^1': 'FD',  # 平仓卖出(平多仓)
}

limitPriceType = ['openPrice', 'preClosePrice']

AShare_exp = '.*[SH$|SZ$]'
Afuture_exp = '.*CFE$'


tradeAcctTypeToEXP = {
    'G20': AShare_exp,
    'G2A': Afuture_exp,
    'S0': AShare_exp,
    'G90':AShare_exp
}

tradeAcctToCatsType = {
    'CASH': 'G20',
    'FUTURE': 'G2A'
}

catsTypeToAccountType = {
    'G20': 'CASH',
    'G2A': 'FUTURE'
}

CatsTypeTotradeAcct = {
    'G20': 'CASH',
    'G2A': 'FUTURE',
    'S0': 'CASH',
    'G90':'CASH'
}

min_buy_volume = 100

aiSideToCatsSide = {
    1: 1,
    -1: 2
}
