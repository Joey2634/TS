# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/2/3 下午1:33
# @Author : lxf
# @File : futureManager.py
# @Project : ai-investment-manager

import logging

import arrow
import pandas as pd
from utils.AiData import which_table, getTradeSectionDates
from collections import defaultdict

from utils.GetContract import getContract
from utils.listTostrforSql import tostr
from configs.Database import oracle, mysql
from configs.tableConfig import account


class futureManager():

    def __init__(self, windInfo, env='dev', mode='backtest'):
        """
        mode : prod:生产/mock:模拟/test:交易系统测试环境/backtest:回测
        """
        self.env = env
        self.mode = mode
        self.windInfo = windInfo
        self.logger = logging.getLogger('futureManager')
        self.betaInfo = defaultdict(lambda: 1)
        # 需要从现货往期货划拨的资金。默认值0
        self.moveCashToFutureAccount = self._loadCashNeedMove()

    def loaddata(self, main_codes, start_date, end_date, windInfoDict):
        sccode = list(set([code.split(".")[0] for code in main_codes]))
        with oracle() as cursor:
            cfuturesdesc = self._load_CFUTURESDESCRIPTION(cursor, sccode, start_date, end_date)
            future_codes = cfuturesdesc.S_INFO_WINDCODE.values.tolist()
            self.windInfo['CFUTURESCONTRACTMAPPING'] = self._load_CFUTURESCONTRACTMAPPING(cursor, future_codes)
            self.windInfo['CFUTURESCONTPRO'] = self._load_CFUTURESCONTPRO(cursor, future_codes)
            self.windInfo['CFUTURESMARGINRATIO'] = self._load_CFUTURESMARGINRATIO(cursor, future_codes)

        [windInfoDict[which_table(code)]['codes'].add(code) for code in future_codes]
        [windInfoDict[which_table(code)]['fields'].update(['S_DQ_OPEN', 'S_DQ_CLOSE', 'S_DQ_SETTLE', 'S_DQ_PRESETTLE'])
         for code in future_codes]

    ## **********************************************************************************************
    def get_future_code(self, trade_date, maincode):
        """
        获取主力合约指定日期对应的合约代码
        """
        # mapdata = self.windInfo['CFUTURESCONTRACTMAPPING']
        # mapdata = mapdata[(mapdata['S_INFO_WINDCODE'] == maincode) &
        #                   (mapdata['STARTDATE'] <= trade_date) &
        #                   (mapdata['ENDDATE'] >= trade_date)]
        # futurecode = mapdata['FS_MAPPING_WINDCODE'].values[0]
        return getContract(trade_date, maincode, 0, season_con=False)
    ## **********************************************************************************************

    def get_margin_ratio(self, trade_date, futurecode):
        """
        获取合约对应的保证金率
        """
        margindata: pd.DataFrame = self.windInfo['CFUTURESMARGINRATIO']
        margindata = margindata[(margindata['S_INFO_WINDCODE'] == futurecode) &
                                (margindata['TRADE_DT'] <= trade_date)]
        # margindata.sort_values(by='TRADE_DT')
        marginRatio = margindata.MARGINRATIO.values[-1]
        return marginRatio

    def get_cemultiplier(self, futurecode):
        """
        获取对应合约的合约乘数
        """
        multidata = self.windInfo['CFUTURESCONTPRO']
        multidata = multidata[multidata['S_INFO_WINDCODE'] == futurecode]
        multiplier = multidata.S_INFO_CEMULTIPLIER.values[0]
        return multiplier

    def reset_account_first_trade_date(self, accountInfo: pd.DataFrame, futureConfig: pd.DataFrame, trade_date):
        """
        如果是对冲策略，第一天划拨资金
        """
        self.hedge_strategys = futureConfig.strategy_id.tolist()
        for index, row in accountInfo.copy().iterrows():
            strategy_id = row['strategy_id']
            if strategy_id in self.hedge_strategys:
                total_cash = row['total_asset']
                main_code = futureConfig[futureConfig['strategy_id'] == strategy_id]['main_code'].values[0]
                beta = float(futureConfig[futureConfig['strategy_id'] == strategy_id]['beta'].values[0])
                stockPositionRatio, futurePositionRatio = self.got_balance_stock_ratio(maincode=main_code,
                                                                                       trade_date=trade_date,
                                                                                       beta=beta)
                stockCash = total_cash * stockPositionRatio // 1  # 取整
                futureCash = total_cash - stockCash
                new_account = [
                    [row['strategy_id'], row['trade_date'], row['account_type'], 0, stockCash, stockCash, stockCash],
                    [row['strategy_id'], row['trade_date'], 'FUTURE', 0, futureCash, futureCash, futureCash]
                ]
                accountInfo = accountInfo[accountInfo['strategy_id'] != strategy_id]
                accountInfo = accountInfo.append(pd.DataFrame(data=new_account, columns=account['columns']))
        return accountInfo

    def got_balance_stock_ratio(self, maincode, trade_date, refer_strategy_id='', beta=1.0):
        """
        param:maincode
        param:trade_date
        param:strategy_id
        #资金划拨
        """
        futureCode = self.get_future_code(trade_date, maincode)
        marginRatio = self.get_margin_ratio(trade_date, futureCode)
        stockPositionRatio, futurePositionRatio, cashRatio = self._calucateStockHedgeRatio(marginRatio=marginRatio,
                                                                                           hedgeRatio=beta)
        return stockPositionRatio, futurePositionRatio

    def got_future_ratio_balance_by_itself(self, maincode, trade_date, moveCashRatio=0):
        """
        # 期货账户自平衡时，期货保证金占期货账户的比例
        """
        assert moveCashRatio >= 0, 'moveCashRatioOfFuture need >= 0 ,now:{}'.format(moveCashRatio)
        futureCode = self.get_future_code(trade_date, maincode)
        marginRatio = self.get_margin_ratio(trade_date, futureCode)
        futureBond, cash = self._calucateFutureBlanceRatio(marginRatio, cash_need_move=moveCashRatio)
        return futureBond

    def get_beta_info(self, futureConf):
        """获取所需锚定的多头策略的beta值"""
        target_strategy_ids = list(set(futureConf.refer_to_strategy_id.values.tolist()))
        if target_strategy_ids:
            with mysql(self.env) as cursor:
                strategyids_str = tostr(target_strategy_ids)
                sql = "select strategy_id,beta from performance_backtest where strategy_id in ({}) " \
                      "and benchmark_id = 'strategy'".format(strategyids_str)
                cursor.execute(sql)
                data = cursor.fetchall()
                for row in data:
                    self.betaInfo[row[0]] = row[1]

    def get_future_ratio(self, stockValue, trade_date, main_code, beta):
        """
        根据多头实际目标持仓市值，计算出期货空头对应的保证金
        """
        futureCode = self.get_future_code(trade_date, main_code)
        marginRatio = self.get_margin_ratio(trade_date, futureCode)
        futureBond = stockValue * marginRatio * beta
        return futureBond

    def reset(self, strategy_id, main_code, preTotalAsset, preStockAsset, trade_date, beta):
        """
        重新计算多头和空投的平衡值，并计算出需要移动的资金,正值，代表需要从多头像期货划拨资金。负值，代表需要从空头像多头划拨资金
        """
        stockPositionRatio, futurePositionRatio = self.got_balance_stock_ratio(maincode=main_code,
                                                                               trade_date=trade_date,
                                                                               beta=beta)
        targetStockAsset = preTotalAsset * stockPositionRatio
        needMoveCash = preStockAsset - targetStockAsset
        self.logger.info('strategy:id:{},trade_date:{},nowTotalAsset:{},nowStockAsset:{},targetStockAsset:{},needMoveCash:{}'.format(
            strategy_id, trade_date, preTotalAsset, preStockAsset, targetStockAsset, needMoveCash
        ))
        self.moveCashToFutureAccount[strategy_id] = float(needMoveCash)
        return stockPositionRatio, futurePositionRatio

    def _calucateStockHedgeRatio(self, marginRatio, maxChange=0.1, orginPosition=1, hedgeRatio=1.0):
        """
        x:stockPositionRatio # 股票占比
        y:futurePositionRatio # 空头期货保证金占比
        z:cashRatio #
        r:marginRatio
        h:空头对冲多头的比例
        {x+y+z=1
         x*h=y/r
         z>=y/r*maxChange*1.1}  1.1的意思是  maxChange扣的钱+持仓亏损需要补的保证金
         解得:
            x <= 1/(1+h*r+h*maxChange*1.1) // 0.001 /1000 截取三位小数,既对0.001取整然后除以1000.
        :param marginRatio: 保证金率
        :param maxChange:最大跌幅
        :return:
        """
        stockPositionRatio = min((1 / (1 + hedgeRatio * marginRatio + hedgeRatio * maxChange * 1.1)), orginPosition)
        futurePositionRatio = stockPositionRatio * marginRatio * hedgeRatio
        cashRatio = 1 - stockPositionRatio - futurePositionRatio
        return stockPositionRatio, futurePositionRatio, cashRatio

    def _calucateFutureBlanceRatio(self, marginRatio, maxChange=0.1, cash_need_move=0):
        """
        :param marginRatio: 保证金率
        :param maxChange:最大跌幅
        :param cash_need_move: 需要给多头移动的钱所占期货资产的比例
        期货自平衡，既期货满仓，保证不爆仓的保证金和现金占比

        x = futureBond      # 期货持仓占用保证金
        y = cash            # 现金
        r = marginRatio     # 保证金比例
        z = cash_need_move
        x + y +z = 1
        y >= x /r*maxChange + x*maxChange
        解得： x <= 1-z/(1+maxChange/r+maxChange)
        """
        futureBond = (1 - cash_need_move) / (1 + maxChange / marginRatio + maxChange)
        cash = 1 - futureBond
        return futureBond, cash

    # ---------------------------------------------private func --------------------------------------------------------

    def _load_CFUTURESDESCRIPTION(self, cursor, mian_code, start_date, end_date):
        """
        获取回测时间段内的合约的万得代码及对应的英文名称
        """
        sccode_str = str(mian_code).replace("[", "").replace("]", "")
        sql = "select s_info_windcode,s_info_code,s_info_exchmarket from CFUTURESDESCRIPTION where FS_INFO_SCCODE in ({}) " \
              "and s_info_listdate < '{}' and s_info_delistdate > '{}'".format(
            sccode_str, end_date, start_date
        )
        cursor.execute(sql)
        data = cursor.fetchall()
        columns = ['S_INFO_WINDCODE', 'S_INFO_CODE', 'S_INFO_EXCHMARKET']
        return pd.DataFrame(data, columns=columns)

    def _load_CFUTURESCONTRACTMAPPING(self, cursor, futurecodes):
        """
        获取特定日期主力合约对应的实际合约代码
        """
        futurecodes_str = str(futurecodes).replace("[", "").replace("]", "")
        sql = "select S_INFO_WINDCODE,FS_MAPPING_WINDCODE,STARTDATE,ENDDATE from CFUTURESCONTRACTMAPPING where FS_MAPPING_WINDCODE in ({})".format(
            futurecodes_str)
        cursor.execute(sql)
        data = cursor.fetchall()
        columns = ['S_INFO_WINDCODE', 'FS_MAPPING_WINDCODE', 'STARTDATE', 'ENDDATE']
        return pd.DataFrame(data, columns=columns)


    def _load_CFUTURESCONTPRO(self, cursor, futurecodes):
        """
        获取合约乘数
        """
        futurecodes_str = str(futurecodes).replace("[", "").replace("]", "")
        sql = "select S_INFO_WINDCODE, S_INFO_PUNIT, S_INFO_CEMULTIPLIER, S_INFO_RTD from CFUTURESCONTPRO where s_info_windcode in ({})".format(
            futurecodes_str)
        cursor.execute(sql)
        data = cursor.fetchall()
        columns = ['S_INFO_WINDCODE', 'S_INFO_PUNIT', 'S_INFO_CEMULTIPLIER', 'S_INFO_RTD']
        return pd.DataFrame(data, columns=columns)

    def _load_CFUTURESMARGINRATIO(self, cursor, futurecodes):
        """
        获取保证金率
        """
        futurecodes_str = str(futurecodes).replace("[", "").replace("]", "")
        sql = "select S_INFO_WINDCODE, TRADE_DT, MARGINRATIO/100 as MARGINRATIO from CFUTURESMARGINRATIO WHERE S_INFO_WINDCODE in ({})".format(
            futurecodes_str)
        cursor.execute(sql)
        data = cursor.fetchall()
        columns = ['S_INFO_WINDCODE', 'TRADE_DT', 'MARGINRATIO']
        df = pd.DataFrame(data, columns=columns)
        df.sort_values(by='TRADE_DT', inplace=True)
        return df

    def moveCash(self, account: pd.DataFrame):
        # 划拨资金
        account['moveCash'] = account['strategy_id'].map(self.moveCashToFutureAccount)
        canCut = defaultdict(lambda :defaultdict(lambda :0))
        for index, row in account.iterrows():
            if row['moveCash'] > 0 and row['account_type'] == 'CASH':
                canCut[row['strategy_id']]['CASH'] = -min(row['cash'],abs(row['moveCash']))
                canCut[row['strategy_id']]['FUTURE'] = min(row['cash'],abs(row['moveCash']))
                self.moveCashToFutureAccount[row['strategy_id']] -= min(row['cash'],abs(row['moveCash']))
            elif row['moveCash'] < 0 and row['account_type'] == 'FUTURE':
                canCut[row['strategy_id']]['CASH'] = min(row['cash'],abs(row['moveCash']))
                canCut[row['strategy_id']]['FUTURE'] = -min(row['cash'],abs(row['moveCash']))
                self.moveCashToFutureAccount[row['strategy_id']] += min(row['cash'],abs(row['moveCash']))
        account['canCut'] = account.apply(self._fill_can_cut, axis=1 , can_cut = canCut)
        account['cash'] = account['cash'] + account['canCut']
        account['total_asset'] = account['cash'] + account['position_value']
        account['sod_total_asset'] = account['cash'] + account['position_value']
        account.drop(['moveCash', 'canCut'], axis=1, inplace=True)

    def _fill_can_cut(self, row: pd.DataFrame, can_cut=None):
        """

        """
        if row['account_type'] == 'CASH':
            return can_cut[row['strategy_id']]['CASH']
        elif row['account_type'] == 'FUTURE':
            return can_cut[row['strategy_id']]['FUTURE']
        else:
            return 0


    def _loadCashNeedMove(self):
        result = defaultdict(lambda : 0)
        if self.mode == 'backtest':
            pass
        else:
            # 从数据库读取需要移动的现金
            today = arrow.now().date().__str__().replace("-", "")
            preTradeDay = getTradeSectionDates(today, -2)[0]
            with mysql(env=self.env) as cursor:
                sql = "select strategy_id,need_move from fund_allocation where trade_date = %s"
                cursor.execute(sql, preTradeDay)
                data = cursor.fetchall()
                for row in data:
                    result[row[0]] = row[1]
        return result


    def save_cash_info(self,strategy_ids = list()):
        with mysql(self.env, commit=True) as cursor:
            today = arrow.now().date().__str__().replace("-", "")
            sql = "insert into fund_allocation values (%s, %s, %s)"
            rows = [[strategy_id, today, self.moveCashToFutureAccount[strategy_id]] for strategy_id in self.moveCashToFutureAccount if strategy_id in strategy_ids]
            if rows:
                cursor.executemany(sql, rows)

    def update_Cash_info(self,strategy_id = ''):
        with mysql(self.env, commit=True) as cursor:
            today = arrow.now().date().__str__().replace("-", "")
            sql = "update fund_allocation set need_move = %s where strategy_id = %s and trade_date = %s"
            need_move = self.moveCashToFutureAccount[strategy_id]
            cursor.execute(sql,(need_move,strategy_id,today))




