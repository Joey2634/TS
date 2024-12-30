# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/3 下午5:30
# @Author : lxf
# @File : riskManagerLive.py
# @Project : ai_investment_manager
import pandas as pd
from collections import defaultdict

import redis

from configs.Database import mysql, SHARE
from configs.Redis import liveMarketRedisConfig
from utils.AiData import which_table
from risk.RiskManager import RiskManager
from utils.listTostrforSql import tostr


class riskManagerLive(RiskManager):
    """

    """

    def __init__(self, env='dev',
                 mode='test',
                 assetInfos: pd.DataFrame = None,
                 marketData: dict = None,
                 trade_date = '',
                 pre_date = '',
                 strategy_configs: list = None,
                 risk_configs: dict = None,
                 tradingServer=None):
        super(riskManagerLive, self).__init__(
            env=env,
            strategy_configs=strategy_configs,
            risk_configs=risk_configs,
            marketData=marketData
        )
        self.mode = mode
        self.trade_date = trade_date
        self.pre_date = pre_date
        self.tradingServer = tradingServer
        self.assetInfo = assetInfos
        self.LS = defaultdict(lambda: 1)
        self._add_extra_asstinfo()
        self.getForbiddenSellPool()



    def run(self, todayTargetPosition, prePosition, preAsset, todayAsset, todayAccount):
        self.logger.info('preAsset:\n{}'.format(preAsset.to_string()))
        self.logger.info('nowAsset:\n{}'.format(todayAsset.to_string()))
        filterTargetRatioByStopLoss = self.filterByStopLoss(preAsset)
        self.logger.info('filterByStopLoss:\n{}'.format(filterTargetRatioByStopLoss.to_string()))
        # 通过最大回撤计算出目标仓位值
        filterTargetRatioByDrawDown = self.filterByMaxDrawDown()
        self.logger.info('filterByDrawDown:\n{}'.format(filterTargetRatioByDrawDown.to_string()))

        # 查看期货配置，判断是否需要reset，并计算出目标仓位
        filterTargetRatioByFuture, targetRatioOfAsset = self.filterByFutureConf(todayAsset, todayAccount)
        # 重新计算今日目标仓位
        todayTargetPosition = self.adjustTodayTargetPosition(todayTargetPosition,
                                                             filterTargetRatioByDrawDown,
                                                             filterTargetRatioByStopLoss,
                                                             filterTargetRatioByFuture,
                                                             prePosition=prePosition,
                                                             todayAsset=todayAsset)
        self.logger.info('adjustTargetPosition before concentration:\n{}'.format(todayTargetPosition.to_string()))
        # 过集中度
        targetAdjustPosition = self.concentrationRatio(todayTargetPosition,
                                                       prePosition=prePosition,
                                                       preAsset=todayAsset)
        self.logger.info('adjustTargetPosition after concentration:\n{}'.format(targetAdjustPosition.to_string()))
        # 根据是否需要对冲，计算期货仓位占比
        targetAdjustPosition = self.dealWithHedge(targetAdjustPosition, todayAsset, todayAccount, targetRatioOfAsset)
        self.logger.info('T0TargetPosition:\n{}'.format(self.T0TargetPosition.to_string()))
        targetAdjustPosition = targetAdjustPosition[['strategy_id', 'trade_date', 'LS', 'windcode', 'target_ratio']]
        return targetAdjustPosition



    # ---------------------------------------- class method ------------------------------------------------------------


    @classmethod
    def updateWindInfoTables(self,infoTables:dict, strategy_configs=None, risk_configs=None, security_list=None):
        """
        分析策略配置和风控配置，告知外层需要预加载的数据
        """
        self.strategyConfigs = strategy_configs
        self.riskConfigs = risk_configs
        # 解析策略配置和风控配置
        self.analysis_risk_config(strategy_configs=strategy_configs,riskConfigs=risk_configs)
        for code in self.defaultReplaceMents.values():
            if which_table(code): security_list.add(code)
        self.maxPreDays = self.maxDrawDownConf.days.max()
        # 最大回撤对应指数
        for code in self.maxDrawDownConf['code'].values.tolist():
            if code != 'NETVALUE' and "." in code:
                tableName = which_table(code)
                infoTables[tableName]['codes'].add(code)
                infoTables[tableName]['fields'].update(['TRADE_DT', 'S_INFO_WINDCODE','S_DQ_CLOSE'])


    def getForbiddenSellPool(self,side='SELL'):
        #
        condition  = 'able2sell' if side =='SELL' else 'able2buy'
        with mysql(SHARE) as cursor:
            sql = "select windcode from restrict_security_list where {} = 'N' ".format(condition)
            cursor.execute(sql)
            data = cursor.fetchall()
        if self.mode == 'prod':
            self.noBuyingPool.update([row[0] for row in data])
            self.logger.info('now no sell poll:{}'.format(self.noBuyingPool))

    # ----------------------------------------- private funcs ----------------------------------------------------------


    def _cal_drawDownByCode(self, row: pd.Series):
        """
        根据最大回撤配置里的code，days来计算出响应的最大回撤
        :param row:
        :return:
        """
        if row.empty:return 0
        if row['code'] == 'NETVALUE':
            strategy_net_values = self.assetInfo[self.assetInfo['strategy_id'] == row['strategy_id']]['net_value'][-int(row['days']):]
            max_drawdown = self.max_drawdown(strategy_net_values)
        elif not which_table(row['code']):
            strategy_net_values = self.assetInfo[self.assetInfo['strategy_id'] == row['code']]['net_value'][-int(row['days']):]
            max_drawdown = self.max_drawdown(strategy_net_values)
        else :
            tablename = which_table(row['code'])
            marketData = self.marketData[tablename].query("TRADE_DT<'{}'".format(self.trade_date)).query("S_INFO_WINDCODE=='{}'".format(row['code']))
            code_net_values = marketData['S_DQ_CLOSE'][-int(row['days']):]
            max_drawdown = self.max_drawdown(code_net_values)
        return max_drawdown

    def _add_extra_asstinfo(self):
        # 如果最大回撤配置了以本策略以外的某个策略为判断标准，加载这个策略的资产信息。
        maxDrawdownTypes = set(self.maxDrawDownConf['code'].values.tolist())
        extra_strategy_ids=[code for code in maxDrawdownTypes if not which_table(code)]
        extra_strategy_ids = list(set(extra_strategy_ids) - set(self.assetInfo.strategy_id.tolist()))
        if 'NETVALUE' in extra_strategy_ids: extra_strategy_ids.remove('NETVALUE')
        print("extra_strategy_ids:{}".format(extra_strategy_ids))
        self.assetInfo = self.assetInfo.append(self._getAssetByStrategy_id(extra_strategy_ids))

    def _getAssetByStrategy_id(self,strategy_ids):
        if not strategy_ids:return pd.DataFrame()
        strategys_str = str(strategy_ids).replace("[", "").replace("]", "").strip(",")
        sql = "SELECT strategy_id,trade_date,position_value,cash,total_asset,sod_total_asset,total_pnl,net_value" \
              " FROM asset where strategy_id in ({}) order by trade_date".format(
            strategys_str)
        with mysql(self.env) as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
            df = pd.DataFrame(list(data),
                              columns=['strategy_id', 'trade_date', 'position_value', 'cash', 'total_asset',
                                       'sod_total_asset', 'total_pnl', 'net_value'])
            df['trade_date'] = df['trade_date'].astype(str)
        return df

    def _get_one_future_value(self, maincode):
        """
        获取当前合约一手的市值和花费的保证金
        """
        futureCode = self.futureManager.get_future_code(self.trade_date, maincode)
        if self.mode in ('prod', 'test'):
            price = self.tradingServer.getStkInfo(futureCode).newPrice
        elif self.mode == 'mock':
            redis_cli = redis.StrictRedis(**liveMarketRedisConfig)
            marketinfo = redis_cli.lrange(futureCode, 0, 0)
            price = eval(marketinfo[0])['lastPrice'] / 10000
        marginRatio = self.futureManager.get_margin_ratio(self.trade_date, futureCode)
        contractTimes = self.futureManager.get_cemultiplier(futureCode)
        oneFutureValue = price * contractTimes
        oneFutureCost = price * contractTimes * marginRatio
        return oneFutureValue, oneFutureCost


    def _getFullFutureValue(self, stockTargetPositionValue, nowStockPositionValue):
        # 生产需要跟当时真实的仓位对比
        return min(stockTargetPositionValue, nowStockPositionValue)