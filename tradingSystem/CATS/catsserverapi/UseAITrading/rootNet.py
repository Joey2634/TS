#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:rootNet.py
@time:2020/06/01
"""
import traceback
import warnings
from collections import defaultdict

import arrow
import pandas as pd
from configs.riskConfig import FUTURE_ENDS
from tradingSystem import Order
from configs.Database import mysql, Database
from tradingSystem.rootNet.RootNetTrading import RootNetTrading
from tradingSystem.CATS.catsserverapi.catsConfig import futureEnds, CatsTypeTotradeAcct
from tradingSystem.CATS.catsserverapi.catsDictionary import CASH, TOTALASSET, POSITIONASSET
from utils.Date import getTradeSectionDates

strategyEnvToTradingEnv = {
    'prod': 'prod',
    'dev': 'test'
}


class rootNet():

    def __init__(self, env='dev', mode='test', commit=True):
        self.env = env
        self.mode = mode
        self.commit = commit
        self.trade_date = str(arrow.now().date())
        self.pre_trade_date = self.pre_date = getTradeSectionDates(self.trade_date, -2)[0]
        self.tradingServer = RootNetTrading(env=mode)
        self.userAcctInfo = defaultdict(dict)
        self.accountToStrategyid = {}  # 匹配账户与策略id
        self.syst_id = 'rootNet'
        self.security_type = {}
        self.need_change_cash = 0
        self.codesStorage = {'000001.SH', '000300.SH', '399001.SZ'}
        self.tradeTypeToInt = {
            'B': (1, 1),  # 股票买入
            'S': (-1, 1),  # 股票卖出
            'B/OPEN': (1, 1),  # 开多仓
            'S/OPEN': (1, -1),  # 开空仓
            'B/CLOSE': (-1, -1),  # 平空仓
            'S/CLOSE': (-1, 1)  # 平多仓
        }

    def getPriceInfo(self, windcode):
        return self.tradingServer.getStkInfo(windcode)

    def login(self, acct_id, acct_pwd, opt_id, opt_pwd):
        """
        :return:
        """
        self.tradingServer.login(acctId=acct_id, acctPwd=acct_pwd,
                                 optId=opt_id, optPwd=opt_pwd)

    def close(self):
        self.tradingServer.disconnect()

    def getCashAndAssert(self):
        """
        :return: {account:(cash,position_value,totalAsset)}
        """
        result = {}
        fundInfo = self.tradingServer.getFundInfo()
        for account, info in fundInfo.items():
            position_value = info.get('currentStkValue', 0)+info.get('marginUsedAmt', 0)
            cash = info['usableAmt'] + info['tradeFrozenAmt']
            totalAsset = cash + position_value
            result[account] = (cash, position_value, totalAsset)
        return result

    def getAccountInfoByStrategyidsAndLogin(self, strategy_ids):
        """
        根据策略id获取账户信息
        """
        sql_user = "select sys_id,user_acct,user_acct_pwd from user_account"
        with mysql(self.env) as cursor:
            cursor.execute(sql_user)
            data = cursor.fetchall()
            for row in data:
                self.userAcctInfo[row[0]]['user_acct'] = row[1]
                self.userAcctInfo[row[0]]['user_acct_pwd'] = row[2]

        self.strategids_str = str(strategy_ids).replace("[", "").replace("]", "").strip(",")
        sql_cash = "select strategy_id,sys_id,acct_type,cats_acct_type,trade_acct,trade_acct_pwd from cash_account where strategy_id in ({})".format(
            self.strategids_str)
        with mysql(self.env, cursor_type='dict') as cursor:
            cursor.execute(sql_cash)
            data = cursor.fetchall()
            for row in data:
                if row['sys_id'] == 'rootNet':
                    self.tradingServer.login(acctId=row['trade_acct'],
                                             acctPwd=row['trade_acct_pwd'],
                                             optId=self.userAcctInfo[row['sys_id']]['user_acct'],
                                             optPwd=self.userAcctInfo[row['sys_id']]['user_acct_pwd'],
                                             acctType=row['acct_type'])
                    self.accountToStrategyid[row['trade_acct']] = row['strategy_id']
                    self.security_type[row['trade_acct']] = row['cats_acct_type']
                else:
                    warnings.warn("not support sys_id:{} of strategy:{}".format(row['sys_id'], row['strategy_id']))

    def _get_pre_sod_total_asset(self, strategy_id, trade_date, account_type):
        with mysql(self.env) as cursor:
            sql = "select total_asset from account where strategy_id = %s and trade_date = %s and account_type = %s"
            cursor.execute(sql, (strategy_id, trade_date, account_type))
            data = cursor.fetchall()
            if data:
                return data[0]
            else:
                return None

    def getPosition(self, tradeAcct=''):
        """
        :return:
        """
        param = {'acct': [tradeAcct]} if tradeAcct else {}
        positions = self.tradingServer.getPositions(where=param)
        return positions

    def getTrades(self, tradeAcct=''):
        """

        :return:
        """
        param = {'acct': [tradeAcct]} if tradeAcct else {}
        trades = self.tradingServer.getTrades(where=param)

        return trades

    def store_position(self):

        positions = self.getPosition()
        if isinstance(positions, pd.DataFrame):
            if positions.empty:
                print("今日持仓为空!")
                return
        else:
            if not positions:
                print("今日持仓为空!")
                return
        positions['strategy_id'] = positions['ACCOUNT'].map(self.accountToStrategyid)
        rows = []
        for index, row in positions.iterrows():
            rows.append((row['strategy_id'], self.trade_date, row["LS"], row['WIND_CODE'],
                         CatsTypeTotradeAcct[self.security_type[row['ACCOUNT']]],
                         row['POSITION'], row['AMOUNT']))
            self.codesStorage.add(row['WIND_CODE'])
        sql_insert = "insert into position (strategy_id,trade_date,LS,windcode,account_type,volume,amount) values (%s,%s,%s,%s,%s,%s,%s)"
        self.saveToDb('position', sql_insert, rows)

    def store_account(self):
        accountInfo = self.getCashAndAssert()
        print(accountInfo)
        rows = []
        for acct, info in accountInfo.items():
            # (cash,position_value,totalAsset)}
            cash, position_value, totalAsset = info
            strategy_id = self.accountToStrategyid[acct]
            sod_total_asset = self._get_pre_sod_total_asset(strategy_id, self.pre_date,
                                                            CatsTypeTotradeAcct[self.security_type[acct]])
            if sod_total_asset == None:
                sod_total_asset = totalAsset
            rows.append(
                (strategy_id, self.trade_date, CatsTypeTotradeAcct[self.security_type[acct]], position_value, cash,
                 totalAsset, sod_total_asset))
        sql_insert = "insert into `account` (strategy_id,trade_date,account_type,position_value,cash,total_asset,sod_total_asset) " \
                     "values (%s,%s,%s,%s,%s,%s,%s)"
        self.saveToDb('account', sql_insert, rows)

    def store_today_trades(self, ):
        trades = self.getTrades()
        if isinstance(trades, pd.DataFrame):
            if trades.empty:
                print("今日无成交!")
                return
        else:
            if not trades:
                print("今日无成交!")
                return
        # ["WIND_CODE","SECURITY_CODE", "MARKET_TYPE", "SECURITY_NAME",
        # "TRADE_TYPE", "TRADE_PRICE", "TRADE_VOLUME", "TRADE_AMOUNT"]]
        trades = trades
        rows = []
        for index, row in trades.iterrows():
            rows.append((self.trade_date, self.accountToStrategyid[row['ACCOUNT']], row['WIND_CODE'],
                         *self.tradeTypeToInt[row['TRADE_TYPE']],
                         row['TRADE_AMOUNT'], row['TRADE_VOLUME'], row['TRADE_PRICE']))
            self.codesStorage.add(row['WIND_CODE'])
        sql_insert = "insert into trade (trade_date,strategy_id,windcode,BS,LS,notional,volume,price) " \
              "values (%s,%s,%s,%s,%s,%s,%s,%s)"
        self.saveToDb('trade', sql_insert, rows)

    def submitOrder(self, wind_code: str, tradeSide: str, targetVol: int, price: float):
        """
        直接下单
        :param wind_code:wind代码
        :param tradeSide:买卖方向(B/S)
        :param targetVol:目标量
        :param price:委托价格
        :return:
        """
        order = Order(windCode=wind_code, orderType=tradeSide, orderQty=targetVol, orderPrice=price)
        self.tradingServer.sendOrder({self.acct_id: [order]})

    def cancelOrders(self, windcode=''):
        """
        """
        data = self.tradingServer.getOriginalOrder()
        cancelkeys = self.getCancelKeys(data, windcode)
        self.tradingServer.cancelOrder(cancelkeys)

    def getCancelKeys(self, df, windcode=''):
        """
        通过条件获取原始订单信息,处理dataframe后返回acctid^^exchid^^contractNum 组成的id列表
        :param where:筛选条件{}
        :return:列表[id,...]
        """
        if isinstance(df, pd.DataFrame):
            if not df.empty:
                df = df[df["CANCELABLE"] == 'Y']
                if windcode:
                    df = df[df['WIND_CODE'] == windcode]
        else:
            if not df:
                return []
        ids = df.CANCEL_KEY.values
        return ids

    def getWindCodeAndMMF(self):
        sql = "select attribute,value from strategy_static_configs where strategy_id = %s"
        result = {}
        with mysql(self.env) as cursor:
            cursor.execute(sql, self.strategy_id)
            data = cursor.fetchall()
            if data:
                for row in data:
                    result[row[0]] = row[1]
        return result

    def getPositionRatioOfMMF(self, windCode=''):
        sql = "select target_ratio from target_position where strategy_id = %s and windcode = '%s'"
        with mysql(self.env) as cursor:
            cursor.execute(sql, (self.strategy_id, windCode))
            data = cursor.fetchall()
            if data:
                return data[0]
            else:
                return 0

    def storeClosePrice(self):
        rows = []
        closePrice = {}
        for windCode in self.codesStorage:
            stkInfo = self.tradingServer.getStkInfo(windCode)
            if windCode.endswith(FUTURE_ENDS):
                preSettlePrice = stkInfo.preSettlementPrice
                preClosePrice = stkInfo.preClosePrice
            else:
                preSettlePrice = stkInfo.closePrice
                preClosePrice = stkInfo.closePrice
            pctchange = (stkInfo.newPrice - preSettlePrice) / preSettlePrice if preSettlePrice else 0
            rows.append(
                (self.trade_date, windCode, stkInfo.newPrice, pctchange, stkInfo.knockQty, stkInfo.knockAmt)
            )
            closePrice[windCode] = (
                self.trade_date, windCode, stkInfo.newPrice, pctchange, stkInfo.knockQty, stkInfo.knockAmt,
                preClosePrice)
        return closePrice


    def saveToDb(self,table, sql_insert, rows):
        with mysql(self.env, commit=self.commit) as cursor:
            try:
                sql_delete = "delete from {} where trade_date = '{}' and strategy_id in ({})".format(table, self.trade_date, self.strategids_str)
                cursor.execute(sql_delete)
                cursor.executemany(sql_insert, rows)
            except:
                traceback.print_exc()