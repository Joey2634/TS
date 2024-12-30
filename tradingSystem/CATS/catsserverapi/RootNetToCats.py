#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:RootNetToCats.py
@time:2020/05/20
"""
import os
import re
import pandas as pd
import traceback
import arrow
from collections import defaultdict
from configs.Database import mysql, DEV
from tradingSystem.CATS.catsserverapi.CATSServer import CATSServer
from tradingSystem.CATS.catsserverapi.UseAITrading.rootNet import rootNet
from tradingSystem.CATS.catsserverapi.models.Account import Account, LocalOsInfo
from tradingSystem.CATS.catsserverapi.models.AlgoParams import AlgoParams
from tradingSystem.CATS.catsserverapi.models.QMOC3Params import QMOC3Params
from tradingSystem.CATS.catsserverapi.catsConfig import tradeSideToStr, futureEnds, \
    windMarket2catsMarket, futureTradeSide, limitPriceType, \
    tradeAcctTypeToEXP, min_buy_volume, aiSideToCatsSide
from AI_Data.database.selectManager import getFuturesContractMultiplierDB

from utils.Date import getTradeSectionDates


class RootNetToCats():
    """
    业务层封装,包含登录,查询,启动算法,停止算法,直接发单等功能
    """

    def __init__(self, env='dev', sysId='rootNet',mode = 'test'):
        self.env = env  # test or prod
        self.mode = mode
        self.trade_date = str(arrow.now().date())
        self.sysId = sysId
        self.security_type = 'CASH'
        self.margin_ratio = 1
        self.LS = 1
        self.positionAsset = defaultdict(lambda: 0)
        self.need_change_cash = 0
        self.rootNet = None
        self.nowCASH = 0
        self.solib_path = os.path.dirname(__file__)+"/libs"
        self.tradingStyle = self._getTradingStyle()
        self.algoidToOrderModel = {
            'AITWAP3':AlgoParams,
            'QMOC3':QMOC3Params
        }
        pass

    def getOrders(self, strategyid, trade_date='', model=None, env='', regexp='-$'):
        """
        从数据库获取今日订单
        :return:
        """
        orders = []
        if not trade_date:
            date = self.trade_date
        else:
            date = trade_date
        dbenv = env if env else self.env
        sql = "select strategy_id,windcode,volume,LS,BS from target_order where strategy_id = %s and trade_date = %s and windcode regexp %s"
        with mysql(dbenv) as cursor:
            regexp = tradeAcctTypeToEXP.get(self.catsServer.acctInfo.tradeAcctType, regexp)
            cursor.execute(sql, (strategyid, date, regexp))
            data = cursor.fetchall()
            if data:
                for order in data:
                    targetVol = int(order[2])
                    if targetVol == 0:
                        continue
                    tradeSide = aiSideToCatsSide[int(order[4])]
                    volume = targetVol if targetVol > 0 else targetVol * -1
                    if model:
                        params = model(symbol=order[1], tradeSide=tradeSide, targetVol=volume)
                    else:
                        params = AlgoParams(symbol=order[1], tradeSide=tradeSide, targetVol=volume, ls=order[3])
                    orders.append(params)
        return orders

    def getOrdersFromDF(self,orderDF:pd.DataFrame,strategy_id,model=AlgoParams, regexp='-$'):
        orders = []
        target_order = orderDF[orderDF['strategy_id'] == strategy_id]
        # endswith = tradeAcctTypeToEndsWith.get(self.catsServer.acctInfo.tradeAcctType)
        # target_order = target_order[target_order.windcode.str.endswith(endswith)]
        regexp = tradeAcctTypeToEXP.get(self.catsServer.acctInfo.tradeAcctType, regexp)
        target_order = target_order[target_order['windcode'].apply(lambda x:bool(re.match(regexp,x)))]
        for index,row in target_order.iterrows():
            targetVol = int(row['volume'])
            if not targetVol:continue
            orders.append(model(symbol=row['windcode'],
                                tradeSide = aiSideToCatsSide[row['BS']],
                                targetVol=targetVol,
                                limitPrice = float(row['price']),
                                ls=row['LS']))

        return orders

    def loadAlgoConfig(self, strategy_id='', algo_type='AITWAP3'):
        """
        获取algo配置
        :return:
        """
        result = defaultdict(lambda :defaultdict())
        sql = "select strategy_id,trade_type,windcode,algo_type,start,`end`,limit_price,minOrderAmt,participateRate,tradingStyle from algo_config where strategy_id = %s and algo_type = %s"
        with mysql(self.env, cursor_type='dict') as cursor:
            cursor.execute(sql, (strategy_id, algo_type))
            data = cursor.fetchall()
            for d in data:
                result[d['windcode']][d['trade_type']] = d
        self.AlgoConfig = result

    def getConfig(self, wind_code, trade_side):
        # 以标的->交易方向->default的优先级顺序,寻找配置
        trade_side = str(trade_side)
        config = self.AlgoConfig[wind_code].get(tradeSideToStr[trade_side])
        if not config:
            config = self.AlgoConfig[wind_code].get("*")
        if not config:
            config = self.AlgoConfig['*'].get(tradeSideToStr[trade_side])
        if not config:
            config = self.AlgoConfig['*'].get('*')
        return config


    def getAccountInfoByDB(self):
        user_account, cash_account = self._getAccountFromDB()
        if not user_account or not cash_account: return []
        for userInfo in user_account:
            if userInfo['sys_id'] == 'CATS':
                self.catsAcct = userInfo.get('user_acct')
                self.catsAcctPwd = userInfo.get('user_acct_pwd')
            elif userInfo['sys_id'] == 'rootNet':
                self.optId = userInfo.get('user_acct')
                self.optPwd = userInfo.get('user_acct_pwd')
        return [(Account(CATS_ACCT=self.catsAcct, CATS_PWD=self.catsAcctPwd, TRADE_ACCT=cashInfo['trade_acct'],
                         TRADE_PWD=cashInfo['trade_acct_pwd'], TRADE_ACCTTYPE=cashInfo['cats_acct_type']),
                 cashInfo['strategy_id']) for cashInfo in cash_account]

    def login(self, acctInfo, localInfo):
        """
        登录
        :param acctInfo:
        :param localInfo:
        :return:
        """
        try:
            self.catsServer = CATSServer(env=self.mode, acct_info=acctInfo, local_info=localInfo,so_path=self.solib_path)
            self.catsServer.initService()
            self.catsServer.catsLogin()
            if self.catsServer.catsLoginedSucessed:
                self.catsServer.catsTradeAcctLogin()
                if self.catsServer.catsTradeLoginedSucessed:
                    # print('login sucessed!')
                    return True
        except:
            traceback.print_exc()
            return False

    def startAlgo(self, algoParams):
        self.catsServer.catsStartAlgo(algoId='AITWAP3', startParams=algoParams)

    def getCash(self):
        assert self.catsServer.catsLoginedSucessed
        assert self.catsServer.catsTradeLoginedSucessed
        self.catsServer.catsGetFundInfo()
        return self.catsServer.catsFundsInfo

    def getPositions(self):
        assert self.catsServer.catsLoginedSucessed
        assert self.catsServer.catsTradeLoginedSucessed
        self.catsServer.catsGetPosition()
        return self.catsServer.Positions

    def subOrderUpdate(self):
        self.catsServer.subOrderUpdate()

    def sendOrder(self, strategy_id, accountinfo, targetOrders = None, algo_id='AITWAP3'):
        model = self.algoidToOrderModel[algo_id]
        if isinstance(targetOrders,pd.DataFrame):
            orders = self.getOrdersFromDF(targetOrders,strategy_id=strategy_id,model=model)
        else:
            orders = self.getOrders(strategyid=strategy_id)
        for order in orders:
            orgin_wind_code = order.symbol
            orgin_trade_side = order.tradeSide
            if orgin_wind_code.endswith(futureEnds):
                order.symbol = orgin_wind_code.split(".")[0] + "." + windMarket2catsMarket[orgin_wind_code.split(".")[1]]
                order.tradeSide = futureTradeSide[str(order.tradeSide) + "^" + str(order.ls)]
                crontractTimes = getFuturesContractMultiplierDB(orgin_wind_code)
                order.targetVol = order.targetVol // crontractTimes
            algoconf = self.getConfig(orgin_wind_code, orgin_trade_side)
            order.account = self.catsServer.acctInfo.tradeAcct
            order.acctType = self.catsServer.acctInfo.tradeAcctType
            if orgin_wind_code.endswith(futureEnds):
                order.beginTime = '145700'
                order.endTime = '150000'
            else:
                order.beginTime = algoconf['start']
                order.endTime = algoconf['end']
            order.limitPrice = algoconf['limit_price']
            order.minOrderAmt = algoconf['minOrderAmt']
            order.participateRate = algoconf['participateRate']
            order.tradingStyle = self.tradingStyle
            algo_id = algoconf['algo_type']
            if not int(order.targetVol):continue
            print(order.getCatsParams())
            self.catsServer.catsStartAlgo(algoId=algo_id, startParams=str(order.getCatsParams()))

    def sendToOrder(self, strategy_id, account, T0TargetOrder,algo_id='AITWAP3'):
        model = self.algoidToOrderModel[algo_id]
        if T0TargetOrder.empty: return
        orders = self.getOrdersFromDF(T0TargetOrder, strategy_id=strategy_id, model=model)
        for order in orders:
            algoconf = self.getConfig(order.symbol, order.tradeSide)
            order.account = self.catsServer.acctInfo.tradeAcct
            order.acctType = self.catsServer.acctInfo.tradeAcctType
            order.beginTime = algoconf['start']
            order.endTime = '144000'
            order.minOrderAmt = algoconf['minOrderAmt']
            order.participateRate = algoconf['participateRate']
            order.tradingStyle = 1
            if not int(order.targetVol): continue
            print(order.getCatsParams())
            self.catsServer.catsStartAlgo(algoId=algo_id, startParams=str(order.getCatsParams()))


    def sendOrderOneCode(self, symbol, tradeSide, targetVol, algo_idwhere='AITWAP3', tradingStyle='2', limitPrice='0'):
        order = AlgoParams(symbol=symbol, tradeSide=tradeSide, targetVol=targetVol)
        order.account = self.catsServer.acctInfo.tradeAcct
        order.acctType = self.catsServer.acctInfo.tradeAcctType
        algoconf = self.getConfig(symbol, tradeSide)
        order.beginTime = algoconf['start']
        order.endTime = algoconf['end']
        order.limitPrice = limitPrice
        order.minOrderAmt = algoconf['minOrderAmt']
        order.participateRate = algoconf['participateRate']
        order.tradingStyle = tradingStyle
        print(order.getCatsParams())
        # self.catsServer.catsStartAlgo(algoId=algo_id,startParams=str(order.getCatsParams()))
        self.saveToCsv(order, filename='orderToCsv/todayOrderT0_{}_{}.csv')
        pass

    def sendOrderToQMOC(self, orders, algoId='QMOC3'):
        for order in orders:
            if order.targetVol <= 0:
                continue
            order.account = self.catsServer.acctInfo.tradeAcct
            order.acctType = self.catsServer.acctInfo.tradeAcctType
            order.beginTime = '145700'
            order.stopPrice = 0
            self.catsServer.catsStartAlgo(startParams=str(order.getCatsParams()), algoId=algoId)


    def saveToCsv(self, order, filename='orderToCsv/todayOrder_{}_{}.csv'):
        # 将本次启动的算法实例参数,按照cats客户端可识别的格式储存到文件.
        fields = [order.acctType, order.account, order.symbol, str(order.targetVol), str(order.tradeSide), 'AITWAP3']
        params = ['beginTime={}'.format(order.beginTime),
                  'endTime={}'.format(order.endTime),
                  'limitPrice={}'.format(order.limitPrice),
                  'participateRate={}'.format(order.participateRate),
                  'tradingStyle={}'.format(order.tradingStyle)
                  ]
        fields_str = ",".join(fields) + ","
        params_str = ";".join(params)
        row = fields_str + params_str + "\n"

        with open(filename.format(self.trade_date, self.env), r'+a') as f:
            f.write(row)

    def storePosition(self, positons, strategy_id):
        # 储存持仓
        if positons:
            rows = []
            for windcode, position in positons.items():
                notional = float(position['costPrice']) * int(position['currentQty'])
                self.positionAsset[strategy_id] += notional
                row = (
                    self.trade_date, strategy_id, self.LS, windcode, '', notional, int(position['currentQty']),
                    self.sysId,
                    self.security_type, self.margin_ratio)
                rows.append(row)
            sql = "insert into eod_position values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            with mysql(self.env, commit=True) as cursor:
                cursor.executemany(sql, rows)

    def storeAssert(self, fundInfo, strategy_id):
        # 储存总资产信息
        sql_select = "select trade_date,total_asset from agg_eod_position_his where trade_date < %s and strategy_id = %s order by trade_date desc"
        with mysql(self.env) as cursor:
            cursor.execute(sql_select, (self.trade_date, strategy_id))
            data = cursor.fetchall()
            pre_total_asset = float(data[0][1])
        cash = fundInfo.currentBalance
        positionAsset = self.positionAsset[strategy_id]
        totalAsset = cash + positionAsset
        sys_eran = totalAsset - pre_total_asset
        sys_pctchange = sys_eran / pre_total_asset
        row = (self.trade_date, strategy_id, self.sysId, self.security_type, sys_pctchange, sys_eran, totalAsset,
               positionAsset, cash, self.need_change_cash)
        sql_insert = "insert into agg_eod_position values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        with mysql(self.env, commit=True) as cursor:
            cursor.execute(sql_insert, row)
            num = cursor.fetchall()

    def storeEodData(self, strategy_id):
        # 储存日终数据
        self.storePosition(self.getPositions(), strategy_id)
        self.storeAssert(self.getCash(), strategy_id)

        # self.storeClosePrice()

    def filterOrderByCash(self, orders,nowCash):
        needCashSum = sum(
            [order.targetVol * order.limitPrice for order in orders if str(order.tradeSide) == '1'])
        for order in orders:
            if str(order.tradeSide) != '1': continue
            cash = order.targetVol*order.limitPrice/needCashSum*nowCash
            max_qty = min(cash / order.limitPrice // min_buy_volume * min_buy_volume, int(order.targetVol))
            order.targetVol = max_qty
        return orders

    def createRootNetServer(self, env,mode, accountinfo):
        if not self.rootNet:
            print(accountinfo)
            self.rootNet = rootNet(env=env,mode=mode)
        tradeAcct = accountinfo.tradeAcct
        if tradeAcct not in self.rootNet.tradingServer.account:
            self.rootNet.login(acct_id=accountinfo.tradeAcct, acct_pwd=accountinfo.tradeAcctPwd, opt_id=self.optId,
                               opt_pwd=self.optPwd)

    def saveInstanceidToDB(self, type='twap'):
        """
        :param type: twap > 调仓, t0 > t0算法
        :return:
        """
        try:
            trade_date = str(arrow.now().date())
            if not self.catsServer.startedInstanceIds: return
            sql = "insert into instanceid_record (trade_date,trade_acct,`type`,instanceid) values (%s,%s,%s,%s)"
            trade_acct = self.catsServer.acctInfo.tradeAcct
            with mysql(self.env, commit=True) as cursor:
                rows = [(trade_date, trade_acct, type, instanceid) for instanceid in self.catsServer.startedInstanceIds]
                cursor.executemany(sql, rows)
        except:
            traceback.print_exc()

    def close(self):
        if self.rootNet:
            self.rootNet.close()

    def _getAccountFromDB(self):
        with mysql(self.env, cursor_type='dict') as cursor:
            sql_user_account = "select sys_id,user_acct,user_acct_pwd from user_account"
            cursor.execute(sql_user_account)
            user_account = cursor.fetchall()

            sql_cash_account = "select strategy_id,sys_id,acct_type,cats_acct_type,trade_acct,trade_acct_pwd from cash_account"
            cursor.execute(sql_cash_account)
            cash_account = cursor.fetchall()
        return user_account, cash_account

    def _getTradingStyle(self):
        try:
            preDay = str(arrow.now().shift(days=-1).date()).replace("-","")
            pre_three_tradeDays = getTradeSectionDates(self.trade_date,-3)
            if preDay not in pre_three_tradeDays  and self.trade_date.replace("-","") in pre_three_tradeDays:
                # 每周第一个交易日
                tradingStyle = 2
            else:
                tradingStyle = 2
        except:

            tradingStyle = 2
        return tradingStyle




def get_rootnet_account_by_trade_acct(env, tradeAcct, strategy_id):
    sql = "select acct_id,acct_pwd,strategy_id,opt_id,opt_pwd from rootnet_account where acct_id = %s and strategy_id = %s"
    with mysql(env) as cursor:
        cursor.execute(sql, (tradeAcct, strategy_id))
        data = cursor.fetchall()
        if data:
            res = data[0]
        else:
            res = []
        return res


if __name__ == '__main__':
    rntc = RootNetToCats(env=DEV,mode='test')
    accountAndstrategy = rntc.getAccountInfoByDB()
    for account, strategy_id in accountAndstrategy:
        print(strategy_id, account)
        rntc.loadAlgoConfig(strategy_id)
        localInfo = LocalOsInfo()
        if rntc.login(account, localInfo):
            rntc.getCash()
            print(rntc.getPositions())
