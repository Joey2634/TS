#!usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file: RiskManager.py
@time: 2020/11/24
"""

import logging
import traceback
from collections import defaultdict
from functools import reduce

import numpy as np
import pandas as pd

from configs.Database import *
from configs.tableConfig import asset, initPandasDataFrame, account
from risk.futureManager import futureManager
from selection.selectionCondition.TRADE_DATE_METHOD import TRADE_DATE_METHOD
from utils.AiData import which_table
from utils.Date import getTradeSectionDates
from utils.Decorator import func_timer
from utils.listTostrforSql import tostr


class RiskManager():
    """
    风控模块，提供集中度，止损，最大回撤等风控功能。
    """
    logger = logging.getLogger('riskManager')

    def __init__(self, env='dev',
                 strategy_configs: list = None,
                 risk_configs: dict = None,
                 target_position: pd.DataFrame = None,
                 adjusted_target_position: list = None,
                 marketData: dict = None):
        self.env = env
        self.strategyConfigs = strategy_configs
        self.riskConfigs = risk_configs
        self.targetPosition = target_position
        self.adjustedTargetPosition = adjusted_target_position
        self.marketData = marketData
        self.LS = defaultdict(lambda: 1)
        self.assetInner = self._initAsset()
        self.assetSpot = self._initSpot()
        self.strategy_ids = [config['strategy_id'] for config in self.strategyConfigs]
        self.logger = logging.getLogger('riskManager')
        # 加载禁卖池
        self.noBuyingPool = set()
        # 额外的部分
        self.T0TargetPosition = self._initT0TargetPosition()
        # 是否需要对冲,之后支持按比例对冲
        self.need_hedge = defaultdict(lambda: False)
        #
        self.accountTargetRatio = defaultdict(lambda: (1, 0))  # {strategy_id:(stockRatio,futureRatio)}
        self.week_trade_date = TRADE_DATE_METHOD('20150101', '20150601', 'DATE_SKEWING=0')
        self.week_first_tradedt = self.week_trade_date._getTradeDates()

    @func_timer
    def run(self, trade_date, preAsset=None, prePosition=None, df_commission=None, today_asset=None,
            today_account=None):
        """
        处理一天的targetOrder到adjust_target_position,将结果更新到self.adjusted_target_position
        :return:
        """
        # 1, deal max_draw_down and stop_loss
        # 2, whether need to do hedging use future
        # 3, deal concentration ratio
        # 注释
        self.trade_date = trade_date
        # # --------------------------------β对冲，设定每日默认对冲比例----------------------------------------------------------

        # self.marketData['AIndexEODPrices']

        # 缓存dataframe格式的asset，以便计算最大回撤
        self.assetInner = self.assetInner.append(preAsset)
        self.assetSpot = self.assetSpot.append(today_account)
        todayTargetPosition = self.targetPosition.query('trade_date=="{}"'.format(self.trade_date)).reset_index(
            drop=True)
        # 通过最大止损计算出目标仓位值
        filterTargetRatioByStopLoss = self.filterByStopLoss(preAsset)
        # 通过最大回撤计算出目标仓位值
        filterTargetRatioByDrawDown = self.filterByMaxDrawDown()
        # 查看期货配置，判断是否需要reset，并计算出目标仓位
        filterTargetRatioByFuture, target_ratio_of_totalAsset = self.filterByFutureConf(today_asset, today_account)
        # 通过佣金计算目标仓位值
        filterTargetRatioByCommission = self.filterByCommission(today_asset, df_commission)
        # 重新计算今日目标仓位
        todayTargetPosition = self.adjustTodayTargetPosition(todayTargetPosition,
                                                             filterTargetRatioByDrawDown,
                                                             filterTargetRatioByStopLoss,
                                                             filterTargetRatioByFuture,
                                                             filterTargetRatioByCommission,
                                                             prePosition=prePosition,
                                                             todayAsset=today_asset)
        # 过集中度，对于有期货，股票集中度相对于股票账户的集中度
        targetAdjustPosition = self.concentrationRatio(todayTargetPosition, prePosition, preAsset=preAsset)
        # 根据是否需要对冲，计算期货仓位占比
        targetAdjustPosition = self.dealWithHedge(targetAdjustPosition, today_asset, today_account,
                                                  target_ratio_of_totalAsset)
        targetAdjustPosition = targetAdjustPosition[['strategy_id', 'trade_date', 'LS', 'windcode', 'target_ratio']]
        self.saveData(targetAdjustPosition)
        return targetAdjustPosition

    def concentrationRatio(self, targetPosition, prePosition=None, preAsset=None):
        """
        集中度处理
        :param targetPosition:
        :return:
        """
        # 获取当前策略的集中度上限
        # targetPosition['concentrationRatioMax'] = targetPosition['strategy_id'].map(self.max_concentrationRatio)
        targetPosition['concentrationRatioMax'] = targetPosition.apply(self._get_max_concentrationRatio, axis=1)
        targetPosition['concentrationRatioMid'] = targetPosition.apply(self._get_max_concentrationRatioMid, axis=1)
        # 计算出每个标的是否超出集中度限制，如果超出，计算出超出量
        targetPosition['redundantRatio'] = np.where(
            targetPosition['target_ratio'] - targetPosition['concentrationRatioMax'] > 0,
            targetPosition['target_ratio'] - targetPosition['concentrationRatioMax'], 0)
        # 更新targetRatio到正确的值，既，如果有超出，将值更新到最大值
        targetPosition['target_ratio'] = targetPosition['target_ratio'].values - targetPosition['redundantRatio'].values
        # 遍历每个策略的defaultReplacement类型，并处理
        targetPosition = self.replaceExtraRatio(targetPosition, prePosition, preAsset)
        # 第二遍做集中度筛选
        # 计算出每个标的是否超出集中度限制，如果超出，计算出超出量
        targetPosition['concentrationRatioMax'] = targetPosition.apply(self._get_max_concentrationRatio, axis=1)
        targetPosition['concentrationRatioMid'] = targetPosition.apply(self._get_max_concentrationRatioMid, axis=1)
        targetPosition['redundantRatio'] = np.where(
            targetPosition['target_ratio'] - targetPosition['concentrationRatioMax'] > 0,
            targetPosition['target_ratio'] - targetPosition['concentrationRatioMax'], 0)
        # 更新targetRatio到正确的值，既，如果有超出，将值更新到最大值
        targetPosition['target_ratio'] = targetPosition['target_ratio'].values - targetPosition['redundantRatio'].values
        return targetPosition

    def filterByCommission(self, todayAsset, df_commission):
        """
        通过佣金计算目标仓位值
        """
        if not df_commission.empty:
            print('need move')
        df = pd.merge(todayAsset[todayAsset['trade_date'] == self.trade_date],
                      df_commission[df_commission['trade_date'] == self.trade_date],
                      on=['strategy_id', 'trade_date'])
        # 确保钱够
        df['Commission'] = ((df['sod_total_asset'] - df['need_cash']) / df['sod_total_asset']).round(2) - 0.01
        targetRatio = df.groupby('strategy_id').agg({"Commission": 'min'})
        return targetRatio

    def filterByStopLoss(self, preAsset):
        """
        根据当前策略净值比例，找到所有符合的止损条件.
        :return:
        """
        # 给每一个止损级别赋值当前netvalue
        df = pd.merge(self.stopLossConf, preAsset, on=['strategy_id'])
        # 筛选出符合当前netvalue的止损条件的目标仓位比例
        df['StopLoss'] = np.where(df['net_value'] <= (1 - df['level'] / 100), df['value'], 1)
        targetRatio = df.groupby('strategy_id').agg({"StopLoss": 'min'})
        return targetRatio

    def filterByMaxDrawDown(self):
        """
        根据策略之前一段时间的净值，计算出各种最大回撤，筛选出符合条件的回撤设置。
        :param preAsset:
        :return:
        """
        drawDownType = self.maxDrawDownConf.groupby(['strategy_id', 'code', 'days']).agg(
            {'strategy_id': "first", "code": "first", 'days': "first"})
        drawDownType = drawDownType.reset_index(drop=True)
        # 计算出指数或者策略的回撤
        drawDownType['draw_down'] = drawDownType.apply(self._cal_drawDownByCode, axis=1)
        df = pd.merge(self.maxDrawDownConf, drawDownType, on=['strategy_id', 'code', 'days']).fillna(0)
        # 用目标净值的最大回撤跟配置中回撤设定值对比，符合条件的，取设定值，否则取1
        df['DrawDown'] = np.where(abs(df['draw_down']) >= df['drawdown'] / 100, df['value'] / 100, 1)
        self.logger.info("maxDrawdown:\n{}".format(df.to_string()))
        # 取符合条件的所有最大回撤目标值的最小值
        targetRatio = df.groupby('strategy_id').agg({"DrawDown": 'min'})
        return targetRatio

    def filterByFutureConf(self, preAsset: pd.DataFrame, preAccount: pd.DataFrame):
        """
        如果是对冲策略，获取对冲指数的主力合约代码。
            对于对冲策略，如果需要reset，重新计算多空占比，并更新资金划拨值
        """
        target_ratio_of_totalAsset = defaultdict(lambda: (1, 0))
        for index, row in self.futureConf.iterrows():
            totalAsset = preAsset[preAsset['strategy_id'] == row['strategy_id']]['sod_total_asset'].values[0]
            preStockAccount = preAccount[(preAccount['strategy_id'] == row['strategy_id']) &
                                         (preAccount['account_type'] == 'CASH')]['sod_total_asset'].values[0]
            preFutureAccount = preAccount[(preAccount['strategy_id'] == row['strategy_id']) &
                                          (preAccount['account_type'] == 'FUTURE')]['sod_total_asset'].values[0]
            self.need_hedge[row['strategy_id']] = row['main_code']
            # if self._need_reset(main_code=row['main_code']):
            if self._dynamic_reset(preFutureAccount / preStockAccount):
                beta = \
                    self.futureConf[self.futureConf['strategy_id'] == row['strategy_id']]['beta'].values[0]
                stockPositionRatio, futurePositionRatio = self.futureManager.reset(row['strategy_id'],
                                                                                   row['main_code'],
                                                                                   totalAsset,
                                                                                   preStockAccount,
                                                                                   self.trade_date,
                                                                                   beta=beta)
                # 期货账户自平衡，期货持仓所占资比例
                futurePositionRatioItself = self.futureManager.got_future_ratio_balance_by_itself(
                    maincode=row['main_code'], trade_date=self.trade_date, moveCashRatio=0)
                futureRatioMax = futurePositionRatioItself * preFutureAccount / totalAsset
                target_ratio_of_totalAsset[row['strategy_id']] = (min(preStockAccount / totalAsset, stockPositionRatio),
                                                                  min(futurePositionRatio, futureRatioMax)
                                                                  )
                self.logger.info("need reset : stockPositionRatio:{},futurePositionRatio:{}"
                                 .format(min(preStockAccount / totalAsset, stockPositionRatio),
                                         min(futurePositionRatio, futureRatioMax)))
            else:
                cashNeedMove = self.futureManager.moveCashToFutureAccount[row['strategy_id']]
                self.logger.info('need move cash:{}'.format(cashNeedMove))
                stockPositionRatio = preStockAccount / totalAsset if cashNeedMove <= 0 else (
                                                                                                        preStockAccount - cashNeedMove) / totalAsset
                moveCashRatioOfFuture = abs(cashNeedMove) / preFutureAccount if cashNeedMove < 0 else 0
                futurePositionRatio = self.futureManager.got_future_ratio_balance_by_itself(
                    maincode=row['main_code'], trade_date=self.trade_date, moveCashRatio=moveCashRatioOfFuture)
                futureRatioMax = futurePositionRatio * preFutureAccount / totalAsset
                target_ratio_of_totalAsset[row['strategy_id']] = (min(stockPositionRatio, 1),
                                                                  min(futureRatioMax, 1))
                self.logger.info("need not reset: stockPositionRatio:{},futurePositionRatio:{}"
                                 .format(min(stockPositionRatio, 1),
                                         min(futureRatioMax, 1)))

        targetRatioSumData = [[strategy_id, target_ratio_of_totalAsset.get(strategy_id, (1, 0))[0]] for strategy_id in
                              self.strategy_ids]
        targetRatioSum = pd.DataFrame(data=targetRatioSumData, columns=['strategy_id', 'Future']).set_index(
            'strategy_id')
        self.logger.info("targetRatioSum : \n{}".format(targetRatioSum.to_string()))
        return targetRatioSum, target_ratio_of_totalAsset

    def replaceExtraRatio(self, targetPosition, prePosition=None, preAsset=None):
        if isinstance(prePosition, pd.DataFrame) and isinstance(preAsset, pd.DataFrame):
            self.logger.info("before _dealWithT0 ,targetPosition :\n".format(targetPosition.to_string()))
            targetPosition = self._dealWithT0(targetPosition, prePosition, preAsset)
            self.logger.info("after _dealWithT0 ,targetPosition :\n".format(targetPosition.to_string()))
        for strategy_id, replaceType in self.defaultReplaceMents.items():
            redundantRatioSum = targetPosition[targetPosition['strategy_id'] == strategy_id]['redundantRatio'].sum()
            if not redundantRatioSum: continue
            if replaceType == 'CASH':
                # 现金替代，不用处理，跳过
                self.logger.info('{},defaultReplacement is CASH, pass'.format(strategy_id))
            # 当量子纠缠替代时，需要用 redundantRatio - T0targetPosition中的部分之后，再去替代
            elif replaceType.startswith('PCC'):
                # pcc,量子纠缠替代
                targetPosition = self._dealPCC(targetPosition, strategy_id, replaceType)
            elif replaceType.startswith("STRATEGY"):
                # 用某个策略替代
                targetPosition = self._dealSTRATEGY(targetPosition, strategy_id, replaceType)
            else:
                # 个股替代
                default_code = self.defaultReplaceMents[strategy_id]
                self.logger.info("strategy:{},redundantRationSum:{},replace windcode:{},append it!".format(
                    strategy_id, redundantRatioSum, default_code))
                targetPosition = self._appendOneCode(targetPosition, strategy_id, windcode=default_code,
                                                     ratio=redundantRatioSum)
        targetPosition = targetPosition.groupby(by=['strategy_id', 'trade_date', 'LS', 'windcode'], as_index=False). \
            agg({'target_ratio': "sum", 'concentrationRatioMax': 'first', 'redundantRatio': 'sum'})
        return targetPosition

    def adjustTodayTargetPosition(self, todayTargetPosition, *args, prePosition=None, todayAsset=None):
        """
        经过止损，最大回撤等风控指标后，重新计算每个标的的目标比例
        :param todayTargetPosition:
        :param args:
        :return:
        """
        # 按策略计算今日目标仓位总和
        targetRatioSum = todayTargetPosition.groupby('strategy_id').agg({'target_ratio': 'sum'})
        # 需要过滤的条件
        conditions = list(args) + [targetRatioSum]
        # df = pd.merge(targetRatioSum,)
        # 将根据每个条件计算出的仓位merge到一起
        df = reduce(lambda x, y: pd.merge(x, y, on=['strategy_id'], how='outer'), conditions).fillna(1).reset_index()
        # 获取每个风控条件出来的目标仓位，取最小值
        if 'Commission' in df.columns:
            df['need_cash'] = df['Future'] + df['Commission'] - 1
        else:
            df['need_cash'] = df['Future']
        df['down_stop'] = df.apply(lambda x: min(x['DrawDown'], x['StopLoss'], x['target_ratio']) if not x.empty else 1,
                                   axis=1)
        df['result_ratio'] = df.apply(lambda x: min(x['need_cash'], x['down_stop']) if not x.empty else 1, axis=1)
        df['replacement'] = df.apply(
            lambda x: x['need_cash'] - x['down_stop'] if x['need_cash'] > x['down_stop'] else 0, axis=1)
        # df['result_ratio'] = df.apply(self._getMinRatio, axis=1)
        # 处理持仓在禁卖池中的标的。如果在禁卖池中，从resulting_ratio中直接减去
        df = self._dealWithForbiddenCodesInPosition(df, prePosition, todayAsset)
        targetRatioSum = pd.merge(targetRatioSum, df[['strategy_id', 'result_ratio']], on=['strategy_id'])
        targetRatioSum['change_ratio'] = targetRatioSum['result_ratio'] / targetRatioSum['target_ratio']
        todayTargetPosition = pd.merge(todayTargetPosition, targetRatioSum[['strategy_id', 'change_ratio']],
                                       on=['strategy_id'])
        # 重新计算各标的的目标比例
        todayTargetPosition['target_ratio'] = todayTargetPosition['target_ratio'] * todayTargetPosition['change_ratio']
        # todayTargetPosition.drop(['change_ratio'], inplace=True, axis=1)
        todayTargetPosition = todayTargetPosition[['strategy_id', 'trade_date', 'LS', 'windcode', 'target_ratio']]
        todayTargetPosition = self.cashManage(todayTargetPosition, df)
        return todayTargetPosition

    # def checkPosition(self,targetPosition):
    #     for strategy_id in self.strategy_ids:
    #         position = targetPosition[targetPosition['strategy_id']==strategy_id]
    #         if position.empty and self.cashManagement[strategy_id] != 'CASH':
    #             management = self.cashManagement[strategy_id]
    #             targetPosition = targetPosition.append([{'strategy_id': strategy_id, 'trade_date': self.trade_date,
    #         'LS': self.LS[management], 'windcode': management, 'target_ratio':1}])
    #     return targetPosition

    def cashManage(self, targetPosition, df):
        for strategy_id, replaceType in self.cashManagement.items():
            redundantRatioSum = df[df['strategy_id'] == strategy_id]['replacement'].sum()
            position = targetPosition[targetPosition['strategy_id'] == strategy_id]
            if replaceType == 'CASH': continue
            # 现金替代，不用处理，跳过
            if position.empty:
                targetPosition = targetPosition.append([{'strategy_id': strategy_id, 'trade_date': self.trade_date,
                                                         'LS': self.LS[replaceType], 'windcode': replaceType,
                                                         'target_ratio': 1}])
                continue
            if redundantRatioSum:
                # 个股替代
                targetPosition = targetPosition.append([{'strategy_id': strategy_id, 'trade_date': self.trade_date,
                                                         'LS': self.LS[replaceType], 'windcode': replaceType,
                                                         'target_ratio': redundantRatioSum}])
        targetPosition = targetPosition.groupby(by=['strategy_id', 'trade_date', 'LS', 'windcode'], as_index=False). \
            agg({'target_ratio': "sum"})
        return targetPosition

    def max_drawdown(self, netvalues: pd.Series):
        """
        根据一列series 计算最大回撤
        :param netvalues:
        :return: 百分比
        """
        return netvalues.div(netvalues.cummax()).sub(1).min()

    def max_drawdown_by_rate(self, rateOfRise: pd.Series):
        """
        根据一列series 计算最大回撤(增长率）
        :param netvalues:
        :return: 百分比
        """
        r = rateOfRise.add(1).cumprod()
        # 数据除以累计最大值-1
        dd = r.div(r.cummax()).sub(1).min()
        return dd

    def saveData(self, adjustTargetPosition):
        self.adjustedTargetPosition.extend(adjustTargetPosition.values.tolist())

    def dealWithHedge(self, targetPosition, todayAsset, todayAccount, targetRatioOfTotalAsset):
        """
        处理对冲
        """
        # 最终多头目标仓位
        cash = ['511880.SH', '511990.SH']
        targetPositionSum = targetPosition[~targetPosition['windcode'].isin(cash)].groupby('strategy_id',
                                                                                           as_index=False) \
            .agg({'target_ratio': 'sum'})
        for index, row in targetPositionSum.iterrows():
            # 如果是对冲策略
            if maincode := self.need_hedge[row['strategy_id']]:
                # 是否有因为持仓在禁卖池而减仓的部分，期货对冲时需要将这部分算入
                hasCutRatio = self.needcut[self.needcut['strategy_id'] == row['strategy_id']]['need_cut']
                if hasCutRatio.empty:
                    hasCutRatio = 0
                else:
                    hasCutRatio = hasCutRatio.values[0]
                stockRatio = row['target_ratio'] + hasCutRatio
                # beta = self.gen_beta(0.1,0.2,0.95,0.8)
                beta = self.futureConf[self.futureConf['strategy_id'] == row['strategy_id']]['beta'].values[0]

                todayTotalAsset = todayAsset[todayAsset['strategy_id'] == row['strategy_id']]['sod_total_asset'].values[
                    0]
                # stockAccount = todayAccount[(todayAccount['strategy_id'] == row['strategy_id']) &
                #                                (todayAccount['account_type'] == 'CASH')]['sod_total_asset'].values[0]
                # futureAccount = todayAccount[(todayAccount['strategy_id'] == row['strategy_id']) &
                #                                 (todayAccount['account_type'] == 'FUTURE')]['sod_total_asset'].values[0]
                nowStockPositionValue = todayAccount[(todayAccount['strategy_id'] == row['strategy_id']) &
                                                     (todayAccount['account_type'] == 'CASH')]['position_value'].values[
                    0]
                stockTargetPositionValue = todayTotalAsset * stockRatio
                targetFullfutureValue = self._getFullFutureValue(stockTargetPositionValue, nowStockPositionValue)
                # 对应当前期货一手的市值和花费的保证金
                oneFutureValue, oneFutureCost = self._get_one_future_value(maincode=maincode)
                futureBond = self.futureManager.get_future_ratio(targetFullfutureValue,
                                                                 self.trade_date,
                                                                 maincode,
                                                                 beta=beta)
                if targetFullfutureValue > oneFutureValue:
                    # 如果目标仓位大于1手期货市值，至少买一手
                    futureBond = max(futureBond, oneFutureCost * 1.1)
                futureRatio = futureBond / todayTotalAsset
                futureRatioBlanceByItSelf = targetRatioOfTotalAsset[row['strategy_id']][1]
                self.logger.info(
                    "stockTargetPositionValue:{},futureBond:{},futureRatio:{}".format(stockTargetPositionValue,
                                                                                      futureBond,
                                                                                      futureRatio))
                futureRatio = min(futureRatio, futureRatioBlanceByItSelf)
                futureCode = self.futureManager.get_future_code(self.trade_date, maincode)
                self.LS[futureCode] = -1
                targetPosition = self._appendOneCode(targetPosition, row['strategy_id'],
                                                     windcode=futureCode,
                                                     ratio=futureRatio)

        return targetPosition

    # -------------------------------------------- private funcs -----------------------------------------------------------
    @classmethod
    def _init_stoploss(self, data=None):
        """
        初始化止损条件
        :param data:
        :return:
        """
        data = pd.DataFrame(data=data, columns=['strategy_id', 'level', 'value'], dtype=np.float)
        data['strategy_id'] = data['strategy_id'].astype('str')
        return data

    @classmethod
    def _init_drawdown(self, data=None):
        """
        初始化最大回撤条件
        :param data:
        :return:
        """
        data = pd.DataFrame(data=data, columns=['strategy_id', 'code', 'days', 'drawdown', 'value'], dtype=np.float)
        data['strategy_id'] = data['strategy_id'].astype(np.str)
        data['code'] = data['code'].astype(np.str)
        return data

    @classmethod
    def _init_futureConf(cls, data=None):
        data = pd.DataFrame(data=data, columns=['strategy_id', 'beta', 'main_code'], dtype=np.str)
        data['beta'] = data['beta'].astype('float')
        return data

    def _initAsset(self):
        """
        :return:
        """
        return initPandasDataFrame(asset)

    def _initSpot(self):
        """
        :return:
        """
        return initPandasDataFrame(account)

    def _getMinRatio(self, row: pd.DataFrame):
        """
        获取最小仓位比例
        :param row:
        :return:
        """
        if row.empty: return 1
        return min(row[1:])

    def _cal_drawDownByCode(self, row: pd.Series):
        """
        根据最大回撤配置里的code，days来计算出响应的最大回撤
        :param row:
        :return:
        """
        if row.empty: return 0
        if row['code'] == 'NETVALUE':
            strategy_net_values = self.assetInner[(self.assetInner['strategy_id'] == row['strategy_id']) &
                                                  (self.assetInner['trade_date'] < self.trade_date)]['net_value'][
                                  -int(row['days']):]
            max_drawdown = self.max_drawdown(strategy_net_values)
        elif not which_table(row['code']):
            strategy_net_values = self.assetInner[(self.assetInner['strategy_id'] == row['code']) &
                                                  (self.assetInner['trade_date'] < self.trade_date)]['net_value'][
                                  -int(row['days']):]
            max_drawdown = self.max_drawdown(strategy_net_values)
        else:
            tablename = which_table(row['code'])
            marketData = self.marketData[tablename].query("TRADE_DT<'{}'".format(self.trade_date)).query(
                "S_INFO_WINDCODE=='{}'".format(row['code']))
            code_net_values = marketData['S_DQ_CLOSE'][-int(row['days']):]
            max_drawdown = self.max_drawdown(code_net_values)
        return max_drawdown

    def _dealWithForbiddenCodesInPosition(self, df, prePosition, todayAsset):
        """
        :param df: 当前每个策略的总目标仓位
        :param prePosition:昨日持仓
        :param todayAsset:昨日总资产信息
        :return:
        """
        if not self.noBuyingPool:
            self.needcut = pd.DataFrame(columns=['strategy_id', 'need_cut'], index=['strategy_id'])
            return df
        # 计算出当前持仓中个成分占总资产的占比
        # todayAsset = todayAsset[todayAsset['account_type'] == 'CASH']
        prePosition = pd.merge(prePosition, todayAsset[['strategy_id', 'sod_total_asset']], on=['strategy_id'])
        prePosition['stk_value_ratio'] = prePosition['amount'] / prePosition['sod_total_asset']
        # 如果持仓有在禁卖池中的标的，将这部分比例从目标仓位中减去
        prePosition['need_cut'] = prePosition.apply(
            lambda row: row['stk_value_ratio'] if row['windcode'] in self.noBuyingPool else 0, axis=1)
        self.logger.info('deal forbidden codes:\n{}'.format(prePosition.to_string()))
        self.needcut = needcut = prePosition.groupby('strategy_id').agg({'need_cut': 'sum'}).reset_index()
        self.logger.info('need cut:\n{}'.format(needcut.to_string()))
        df = pd.merge(df, needcut, on=['strategy_id'])
        result1 = df['result_ratio']
        df['result_ratio'] = df['result_ratio'] - df['need_cut']
        df['result_ratio'] = np.where(df['result_ratio'] >= 0, df['result_ratio'], 0)
        df['replacement'] = result1 - df['result_ratio']
        return df

    def _getReplaceCode(self, windcode, corr, length):
        """

        """
        result = []
        # 获取最新的替代标的信息的日期
        replace_info_date = self.codeReplace[(self.codeReplace['windcode'] == windcode) &
                                             (self.codeReplace['trade_date'].str.replace("-", "") <= self.trade_date)][
            'trade_date'].values.tolist()
        if replace_info_date:
            replace_info_date = replace_info_date[0]
        else:
            return result
        # 根据日期，相关度和截取长度，获取符合条件的替代信息
        replaceCodesdf = self.codeReplace[(self.codeReplace['trade_date'] == replace_info_date) &
                                          (self.codeReplace['corr'] > corr) & (
                                                      self.codeReplace['windcode'] == windcode)]
        for index, row in replaceCodesdf.iterrows():
            result.append((row['backup_security'], row['corr']))
        return result[:length]

    def _appendOneCode(self, targetPosition, strategy_id, windcode, ratio):
        targetPosition = targetPosition.append([{
            'strategy_id': strategy_id,
            'trade_date': self.trade_date,
            'LS': self.LS[windcode],
            'windcode': windcode,
            'target_ratio': ratio,
            'redundantRatio': 0,
            'concentrationRatioMax': 0
        }])
        return targetPosition

    def _dealPCC(self, targetPosition, strategy_id, replaceType):
        """
        用量子纠缠替代
        """
        tmpTargetPosition = targetPosition[targetPosition['strategy_id'] == strategy_id]
        for index, row in tmpTargetPosition.iterrows():
            if not row['redundantRatio']: continue
            _, corr, length = replaceType.split(":")
            replaceCodes = self._getReplaceCode(row['windcode'], float(corr), int(length))
            if not replaceCodes:
                self.logger.info("got empty replace codes of code:{},by corr:{}".format(row['windcode'], corr))
                continue
            replaceCorrSum = sum([corrinfo[1] for corrinfo in replaceCodes])
            for replace_code, corr in replaceCodes:
                ratio = corr / replaceCorrSum * row['redundantRatio']
                targetPosition = self._appendOneCode(targetPosition, strategy_id, replace_code, ratio)
        return targetPosition

    def _dealSTRATEGY(self, targetPosition: pd.DataFrame, strategy_id, replaceType):
        # 多出部分用某个策略的成分股替代
        replaceStrategyid = replaceType.split(':')[-1]
        replaceTargetPosition = self.extTargetPosition[(self.extTargetPosition['strategy_id'] == replaceStrategyid) &
                                                       (self.extTargetPosition['trade_date'].str.replace('-',
                                                                                                         '') == self.trade_date)].copy()
        if not replaceTargetPosition.empty:
            # ['strategy_id','trade_date','windcode','LS','target_ratio']
            redundantRatioSum = targetPosition[targetPosition['strategy_id'] == strategy_id].groupby('strategy_id').agg(
                {'redundantRatio': 'sum'}).values.tolist()
            if redundantRatioSum:
                sumRatio = redundantRatioSum[0][0]
                replaceTargetPosition['target_ratio'] = replaceTargetPosition['target_ratio'] * sumRatio
                replaceTargetPosition['strategy_id'] = strategy_id
                replaceTargetPosition['concentrationRatioMax'] = replaceTargetPosition['strategy_id'].map(
                    self.max_concentrationRatio)
                replaceTargetPosition['redundantRatio'] = 0
                targetPosition = targetPosition.append(replaceTargetPosition, ignore_index=True)
        return targetPosition

    def _initT0TargetPosition(self):
        """
        额外的做T的部分，先买后卖

        """
        columns = ['strategy_id', 'trade_date', 'LS', 'windcode', 'target_ratio']
        return pd.DataFrame(columns=columns)

    def _get_max_concentrationRatio(self, row: pd.Series):
        if row.empty: return
        if which_table(row['windcode']) != 'AShareEODPrices': return 1
        if row['windcode'].startswith('300') and row['windcode'].endswith('SZ'):
            return self.max_concentrationGemRatio[row['strategy_id']]
        else:
            return self.max_concentrationRatio[row['strategy_id']]

    def _getratio(self, row: pd.Series):
        # 获取目标仓位，如果需要对冲，修改flag
        if row.empty: return
        if abs(row['draw_down']) >= row['drawdown'] / 100:
            if str(row['value']).endswith('CFE'):
                self.need_hedge[row['strategy_id']] = row['value']
                return 1
            else:
                return row['value']
        else:
            return 1

    def _get_max_concentrationRatioMid(self, row: pd.Series):
        if row.empty: return
        if which_table(row['windcode']) != 'AShareEODPrices': return 1
        max_concentration_mid_times = self.max_concentrationMidRatio[row['strategy_id']] + 1
        if row['windcode'].startswith('300') and row['windcode'].endswith('SZ'):
            return self.max_concentrationGemRatio[row['strategy_id']] * max_concentration_mid_times
        else:
            return self.max_concentrationRatio[row['strategy_id']] * max_concentration_mid_times

    # ------------------------------------------- classmethod ---------------------------------------------------------
    @classmethod
    def updateWindInfoTables(self, infoTables: dict, env='dev', strategy_configs=None, risk_configs=None,
                             security_list=None, keepPosition=None):
        """
        分析策略配置和风控配置，告知外层需要预加载的数据
        """
        self.strategyConfigs = strategy_configs
        self.riskConfigs = risk_configs
        # 解析策略配置和风控配置
        self.analysis_risk_config(strategy_configs=strategy_configs, riskConfigs=risk_configs,
                                  keepPosition=keepPosition)
        self.loadReplaceSecurities(env, security_list)
        self._loadExtraTargetPosition(env, security_list)
        for code in self.defaultReplaceMents.values():
            if which_table(code): security_list.add(code)
        for code in self.cashManagement.values():
            if which_table(code): security_list.add(code)
        # 最大回撤对应指数
        for code in self.maxDrawDownConf['code'].values.tolist():
            if which_table(code):
                tableName = which_table(code)
                infoTables[tableName]['codes'].add(code)
                infoTables[tableName]['fields'].update(['S_DQ_CLOSE'])

    @classmethod
    def analysis_risk_config(self, strategy_configs, riskConfigs, keepPosition={}):
        """
        解析风控配置，使之与策略id匹配
        :return:
        """
        self.max_concentrationRatio = {}
        self.max_concentrationMidRatio = {}
        self.max_concentrationGemRatio = {}
        self.defaultReplaceMents = {}
        self.cashManagement = {}
        self.stopLossConf = self._init_stoploss()
        self.maxDrawDownConf = self._init_drawdown()
        self.futureConf = self._init_futureConf()
        self.hedgeConf = {}
        for strategyConfig in strategy_configs:
            strategy_id = strategyConfig['strategy_id']
            risk_id = strategyConfig.get('risk_id')
            if not riskConfigs.get(risk_id):
                self.max_concentrationRatio[strategy_id] = 1
                self.max_concentrationMidRatio[strategy_id] = 0
                self.max_concentrationGemRatio[strategy_id] = 1
                continue
            risk_config = riskConfigs.get(risk_id)
            self.max_concentrationRatio[strategy_id] = float(risk_config['concentration_ratio'])
            self.max_concentrationMidRatio[strategy_id] = float(risk_config.get('concentration_mid_ratio', 0))
            self.max_concentrationGemRatio[strategy_id] = float(
                risk_config.get('concentration_gem_ratio', float(risk_config['concentration_ratio'])))
            self.defaultReplaceMents[strategy_id] = risk_config['default_replacement']
            self.cashManagement[strategy_id] = risk_config.get('cash_management', 'CASH')
            for k, value in risk_config.items():
                if k.startswith('stop_loss'):
                    self.stopLossConf = self.stopLossConf.append(
                        self._init_stoploss([[strategy_id, float(k.split(':')[1]), float(value)]])
                    )
                if k.startswith('drawdown'):
                    _, code, days, drawdown = k.split(":")

                    self.maxDrawDownConf = self.maxDrawDownConf.append(
                        self._init_drawdown([[strategy_id, code, int(days), float(drawdown), float(value)]])
                    )
                if k.startswith('hedge'):
                    _, beta = k.split(":")
                    self.futureConf = self.futureConf.append(
                        self._init_futureConf([[strategy_id, float(beta), value]])
                    )
            if risk_config.get('keep_position'):
                keepPosition[strategy_id] = True

            self.stopLossConf = self.stopLossConf.sort_values(by=['level'], axis=0)
            self.maxDrawDownConf = self.maxDrawDownConf.sort_values(by=['days', 'drawdown'], axis=0)

    @classmethod
    def loadFutureInfo(self, windInfo, start_date, end_date, windInfoDict, env, mode='backtest'):
        # 判断是否需要期货对冲，如果需要，添加期货所需内容
        # 添加指数对应行情
        self.futureManager = futureManager(windInfo, env, mode=mode)
        future_main_codes = set([value for value in self.futureConf['main_code'].values.tolist()])
        if future_main_codes:
            self.futureManager.loaddata(future_main_codes, start_date, end_date, windInfoDict)
        # 获取所需锚定的多头策略的beta值
        # self.futureManager.get_beta_info(self.futureConf)
        return self.futureManager

    def _add_future(self, maincode='', targetRatio=1):
        """
        # 添加期货
        """
        futureCode = self.futureManager.get_future_code(self.trade_date, maincode)
        marginRatio = self.futureManager.get_margin_ratio(self.trade_date, futureCode)
        stockPositionRatio, futurePositionRatio, cashRatio = self.futureManager._calucateStockHedgeRatio(
            marginRatio=marginRatio, orginPosition=targetRatio)
        return stockPositionRatio, futurePositionRatio, cashRatio

    def _recal_position_ratio(self, targetPosition, strategy_id, changeRatio):
        # 根据要变化的比例，重新计算目标仓位
        targetPosition['target_ratio'] = targetPosition.apply(
            lambda row: row['target_ratio'] * changeRatio if row['strategy_id'] == strategy_id else row['target_ratio'],
            axis=1)

    @classmethod
    def loadReplaceSecurities(self, env, securities):
        """
        加载量子纠缠替代标的所有数据
        """
        columns = ['windcode', 'trade_date', 'backup_security', 'corr']
        try:
            with mysql(env) as cursor:
                min_pcc_corr = [float(info.split(":")[1]) for info in self.defaultReplaceMents.values() if
                                info.startswith('PCC')]
                if min_pcc_corr:
                    min_pcc_corr = min(min_pcc_corr)
                    securities_str = str(list(securities)).replace("[", "").replace("]", "").strip(",")
                    sql = "select windcode,trade_date,backup_security,corr from replace_security_list where windcode in ({}) and corr >= {}".format(
                        securities_str, min_pcc_corr)
                    cursor.execute(sql)
                    data = cursor.fetchall()
                else:
                    data = []
        except:
            self.logger.error('load replaceSecurities error:{}'.format(traceback.format_exc()))
            data = []
        df = pd.DataFrame(data=data, columns=columns)
        df['corr'] = df['corr'].astype('float')
        df = df.sort_values(by=['trade_date', 'corr'], ascending=False)
        securities.update(df.backup_security.values.tolist())
        self.codeReplace = df

    @classmethod
    def _loadExtraTargetPosition(self, env, securities):
        ext_strategies = [
            value.split(":")[1] for value in self.defaultReplaceMents.values() if value.startswith('STRATEGY')
        ]
        columns = ['strategy_id', 'trade_date', 'windcode', 'LS', 'target_ratio']
        data = []
        if ext_strategies:
            stra_str = tostr(ext_strategies)
            with mysql(env) as cursor:
                sql = "select strategy_id,date_format(trade_date,'%Y%m%d') as trade_date,windcode,LS,target_ratio from target_position_backtest where strategy_id in ({})".format(
                    stra_str)
                cursor.execute(sql)
                data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        df['target_ratio'] = df['target_ratio'].astype('float')
        securities.update(df.windcode.values.tolist())
        self.extTargetPosition = df

    def _dealWithT0(self, targetPosition, prePosition, preAccount):
        # 计算出当前持仓中个成分占总资产的占比
        tmpprePosition = pd.merge(prePosition, preAccount[['strategy_id', 'total_asset']], on=['strategy_id'],
                                  how='left')
        tmpprePosition['stk_value_ratio'] = tmpprePosition['amount'] / tmpprePosition['total_asset']
        tmptargetPosition = pd.merge(targetPosition,
                                     tmpprePosition[['strategy_id', 'windcode', 'LS', 'stk_value_ratio']],
                                     on=['strategy_id', 'windcode', 'LS'], how='left')
        tmptargetPosition.fillna(0, inplace=True)
        tmptargetPosition['T0Ratio'] = tmptargetPosition.apply(self._fill_t0_ratio, axis=1)
        tmptargetPosition['redundantRatio'] = tmptargetPosition['redundantRatio'] - tmptargetPosition['T0Ratio']
        self.logger.info("tmpTargetPosition:\n{}".format(tmptargetPosition.to_string()))
        for index, row in tmptargetPosition.iterrows():
            if row['T0Ratio']:
                self.T0TargetPosition = self.T0TargetPosition.append([{
                    'strategy_id': row['strategy_id'],
                    'trade_date': self.trade_date,
                    'LS': self.LS[row['windcode']],
                    'windcode': row['windcode'],
                    'target_ratio': row['T0Ratio'],
                }])
        return tmptargetPosition

    def _need_reset(self, main_code):
        """
        判断是不是reset日，既是否期货移仓换约。
        """
        # 月度调仓代码
        # pre_trade_date = getTradeSectionDates(self.trade_date, -2)[0]
        # if self.futureManager.get_future_code(pre_trade_date, main_code) != self.futureManager.get_future_code(self.trade_date,main_code):
        #     return True
        # else:
        #     return False
        # 周度调仓代码
        # return True

        # ----------------------------------------------------------------------
        pre_trade_date = getTradeSectionDates(self.trade_date, -2)[0]
        if self.futureManager.get_future_code(pre_trade_date, main_code) != self.futureManager.get_future_code(
                self.trade_date, main_code):
            print('reset')
            return True
        # elif pre_trade_date in self.week_first_tradedt:
        #     print('week reset')
        #     return True
        else:
            return False
        # ----------------------------------------------------------------------

    def _dynamic_reset(self, f_s_cashratio):
        if f_s_cashratio >= 0.19:
            return True
        else:
            return False

    def _get_one_future_value(self, maincode):
        """
        获取当前合约一手的市值和花费的保证金
        """
        futureCode = self.futureManager.get_future_code(self.trade_date, maincode)
        table = which_table(futureCode)
        marketInfo = self.marketData[table].query("TRADE_DT=='{}'".format(self.trade_date)).query(
            "S_INFO_WINDCODE=='{}'".format(futureCode))
        if not marketInfo.empty:
            price = marketInfo['S_DQ_SETTLE'].values[0]
        else:
            raise Exception('trade_date:{},code:{}, has no S_DQ_SETTLE'.format(self.trade_date, futureCode))
        marginRatio = self.futureManager.get_margin_ratio(self.trade_date, futureCode)
        contractTimes = self.futureManager.get_cemultiplier(futureCode)
        oneFutureValue = price * contractTimes
        oneFutureCost = price * contractTimes * marginRatio
        return oneFutureValue, oneFutureCost

    def _getFullFutureValue(self, stockTargetPositionValue, nowStockPositionValue):
        # 回测只需返回target
        return stockTargetPositionValue

    def _fill_t0_ratio(self, row: pd.DataFrame):
        if row.empty:
            return 0
        return min(float(row['stk_value_ratio']), float(row['redundantRatio']), float(row['concentrationRatioMid']) -
                   float(row['concentrationRatioMax']))

    def gen_beta(self, ll, l, uu, u, norm=0.4):
        sig_lis = self.marketData['smartTiming'][self.trade_date]
        if (sig_lis[1] == 1):
            return ll
        elif (sig_lis[1] == 0.5):
            return l
        elif (sig_lis[1] == -1):
            return uu
        elif (sig_lis[1] == -0.5):
            return u
        if (sig_lis[0] == 1):
            return ll
        elif (sig_lis[0] == 0.5):
            return l
        elif (sig_lis[0] == -1):
            return uu
        elif (sig_lis[0] == -0.5):
            return u
        else:
            return norm
