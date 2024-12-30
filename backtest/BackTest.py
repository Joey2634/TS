import os, sys
from clearSettle.multiprocessingPage import multiProcessings
from clearSettle.performanceIndex import PerformanceIndex
from utils.listTostrforSql import tostr

path = os.path.dirname(os.path.dirname(__file__))
print(path)
sys.path.append(path)
import traceback
from collections import defaultdict
from clearSettle.ClearSettleBacktest import ClearSettleBacktest
from clearSettle.Period import Period
from configs.Database import mysql
from utils.Date import getTradeSectionDates, getTradeDates
from utils.AiData import getWindData, which_table
from utils.Decorator import func_timer
from risk.RiskManager import RiskManager
from tradeExecution.createOrder.targetOrderBackTest import targetOrderBackTest
from configs.tableConfig import *
import warnings
warnings.filterwarnings(action='ignore')
idx = pd.IndexSlice


class BackTest:

    def __init__(self, strategy_ids: [str], start_date: str, end_date: str, env='dev', log=False):
        if log:
            from utils.logger import setup_logging_by_params
            setup_logging_by_params('backtest')
        self.strategy_ids = strategy_ids
        self.strategy_ids_str = tostr(self.strategy_ids)
        #todo: 交易日
        # self.trade_dates = getTradeDates(start_date, end_date)
        self.trade_dates = [start_date, end_date]
        self.init_account_date: str = start_date
        self.env = env
        with mysql(env, 'dict') as self.cursor:
            self.strategy_configs = self._getStrategyConfig()
        with mysql(env) as self.cursor:
            self.risk_configs = self._getConfig('risk_config', 'risk_id')
            self.performance_configs = self._getConfig('performance_config', 'performance_id')
            # self.am_configs = self._getAssetManagementInfo()
        self.asset = []
        self.account = []
        self.position = []
        self.trade = []
        self.am_fee = []
        self.target_order = []
        self.adjust_position = []
        self.setTargetPosition()
        self._setSecurityPool()
        self._setWindInfo()
        self.riskManager = RiskManager(strategy_configs=self.strategy_configs, risk_configs=self.risk_configs,
                                           target_position=self.target_position,
                                           adjusted_target_position=self.adjust_position,
                                           marketData=self.windInfo)
        self.targetOrder = targetOrderBackTest(strategyConfigs=self.strategy_configs, marketData=self.windInfo,
                                               target_order=self.target_order, security_list=self.security_list,
                                               trade=self.trade,futureManager=self.futureManager)
        self.clearSettle = ClearSettleBacktest(self.strategy_configs, self.windInfo, self.asset, self.account,self.position,
                                               self.trade, self.init_account_date, self.am_configs, self.am_fee, level='INFO')
        self.period = Period(strategy_ids, env, mode='backtest', end_day=self.trade_dates[-1])

    def _setAsset(self):
        init_asset = [[strategy_config['strategy_id'], self.init_account_date, 0, strategy_config['amount'],
                       strategy_config['amount'], strategy_config['amount'], 0, 1, 1] for strategy_config in
                      self.strategy_configs]
        self.asset.extend(init_asset)
        return initPandasDataFrame(asset, init_asset)

    def _setAccount(self):
        init_account = [[strategy_config['strategy_id'], self.init_account_date, 'CASH', 0, strategy_config['amount'],
                         strategy_config['amount'], strategy_config['amount']] for strategy_config in
                        self.strategy_configs]
        self.account.extend(init_account)
        return initPandasDataFrame(account, init_account)
    @func_timer
    def _setSecurityPool(self):
        self.security_list = set(self.target_position['windcode'].values.tolist())



    def _updateStrategyIds(self):
        for k, value in self.risk_configs.items():
            for key in value.keys():
                if key.startswith('drawdown'):
                    _, code, days, drawdown = key.split(":")
                    if not (code == 'NETVALUE' or which_table(code) or code in self.strategy_ids):
                        self.strategy_ids.append(code)
                        print('add id:', code)

    def _getAssetManagementInfo(self):
        self.cursor.execute("select * from am_config")
        res = pd.DataFrame(list(self.cursor.fetchall()),columns=['strategy_id','management_fee','custodian_fee','incentive_fee'])
        res = {i.pop('strategy_id'): i for i in list(res.to_dict('index').values())}
        # 填补资管策略默认参数
        for config in self.strategy_configs:
            if config['strategy_id'] not in res and config['business_type']=='A6':
                res.update({config['strategy_id']:res['default']})
        return res


    @func_timer
    def setTargetPosition(self):
        # # table_name = 'AShareEODPrices'
        # allocation = Allocation(self.strategy_configs, self.allocation_configs, self.trade_dates, self.security_pool,self.windInfo)
        # self.target_position = allocation.run()
        with mysql(self.env) as cursor:

            sql = "select * from target_position where strategy_id in ({})".format(self.strategy_ids_str)
            cursor.execute(sql)
            data = cursor.fetchall()
            self.target_position = pd.DataFrame(data = data, columns=target_position['columns'])
        print(self.target_position)

    @func_timer
    def _getStrategyConfig(self):
        """
        读取策略参数
        """
        sql = "select strategy_id,business_type,selection_id,allocation_id,trade_price,risk_id,amount,performance_id from strategy_config where strategy_id "
        if len(self.strategy_ids) > 1:
            strategy_ids = tuple(self.strategy_ids)
            sql = sql + "in {0}".format(tuple(strategy_ids))
        elif len(self.strategy_ids) == 1:
            sql = sql + "= '{0}'".format(self.strategy_ids[0])
        else:
            exit("No strategy_id")
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    @func_timer
    def _getConfig(self, table, key):
        result = {}
        ids = set(config[key] for config in self.strategy_configs)
        if 'NONE' in ids:
            ids.remove('NONE')
        sql = "SELECT * FROM " + table + " where " + key
        if len(ids) > 1:
            sql = sql + " in {0}".format(tuple(ids))
        elif len(ids) == 1:
            sql = sql + " = '{0}'".format(ids.pop())
        else:
            return
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        for res in data:
            if res[0] not in result:
                result[res[0]] = {}
            result[res[0]][res[1]] = res[2]
        return result

    @func_timer
    def _setWindInfo(self):
        """

        :return: {'tablename1':{'codes':set(),'fields':set()},
                    'tablename2':{'codes':set(),'fields':set()},...
                    }
        """
        windInfoDict = defaultdict(lambda: defaultdict(set))
        #更新所需信息统计表
        # 当没有targetpositoin时 是否保持持仓不变
        keepPosition = defaultdict(lambda: False)
        RiskManager.updateWindInfoTables(windInfoDict, strategy_configs=self.strategy_configs,
                                         risk_configs=self.risk_configs, security_list=self.security_list,
                                         keepPosition=keepPosition)
        targetOrderBackTest.updateWindInfoTables(windInfoDict, strategyConfigs=self.strategy_configs,
                                                 security_pool=self.security_list, keepPosition= keepPosition)
        ClearSettleBacktest.updateWindInfoTables(windInfoDict, performance_configs=self.performance_configs)
        # 根据各个模块搜集的信息获取数据
        self.windInfo = {}
        # sample_size = max(
        #     set(int(self.allocation_configs[config]['sample_size']) for config in self.allocation_configs)) + 1
        # 如果需要，加载期货行情
        for table, info in windInfoDict.items():
            self.windInfo[table] = getWindData(
                table=table, code_list=info['codes'], start_date=market_quotes_start_date,
                end_date=self.trade_dates[-1], fields=info['fields'])

    def saveResult2DB(self, tables = [], condition = ""):
        '''
        存入数据库
        :param tables: 要存库的表名
        :param condition: 筛选条件
        :param delete: 是否删除重复数据
        :return:
        '''
        performance_df = pd.DataFrame(self.performance, columns=performance['columns'])
        performance_df = performance_df.query(condition+"and benchmark_id=='strategy'") if condition else performance_df
        if performance_df.empty:
            print("没有满足条件的策略")
            return
        all_table = {'target_position_backtest': self.target_position.values.tolist(),
                  'adjusted_target_position_backtest':self.adjust_position,
                  'asset_backtest': self.asset,
                  'account_backtest': self.account,
                  'position_backtest': self.position,
                  'trade_backtest': self.trade,
                  'target_order_backtest': self.target_order,
                  'performance_backtest': self.performance,
                  'am_fee_backtest': self.am_fee,
                  'turnover_backtest': self.turnover}
        if tables:
            result={}
            for table in tables:
                data = pd.DataFrame(all_table[table])
                data = data[data[0].isin(performance_df['strategy_id'].values.tolist())]
                result[table] = data.values.tolist()
        else:
            result = all_table
        with mysql(self.env, commit=True) as self.cursor:
            for table, data in result.items():
                if not data:
                    continue
                try:
                    values = str(('%s',) * len(data[0])).replace("'", "")
                    self.cursor.execute("delete from {} where strategy_id in ({})".format(table,str(self.strategy_ids).replace("[","").replace("]","").strip(",")))
                    self.cursor.executemany("insert into {} values {}".format(table, values), data)
                except:
                    print("store data error:table:{},error:{}".format(table,traceback.format_exc()))

    def period_performance(self):
        '''
        分段绩效,只有在插入asset数据的情况下才能跑通
        :return:
        '''
        data = self.period.getPeriodPerformance(self.clearSettle, self.performance_configs, self.am_configs)
        with mysql(self.env, commit=True) as self.cursor:
            table = 'period_performance_backtest'
            values = str(('%s',) * len(data[0])).replace("'", "")
            self.cursor.execute("delete from {} where strategy_id in ({})".format(table, str(
                self.strategy_ids).replace("[", "").replace("]", "").strip(",")))
            self.cursor.executemany("insert into {} values {}".format(table, values), data)
        # 计算换手率
        paras = []
        for mode in self.period.months:
            for id in self.strategy_ids:
                start_date, end_date = self.period.getTimePeriod(id, self.trade_dates[-1], mode)
                paras.append({'strategy_ids':[id], 'env':self.env, 'start_date':start_date, 'end_date':end_date,
                              'mode':mode, 'backtest':True})
        res = multiProcessings(10, paras, PerformanceIndex.turnover)
        with mysql(self.env, commit=True) as cursor:
            values = str(('%s',) * len(res[0])).replace("'", "")
            cursor.execute("delete from turnover_backtest where strategy_id in ({}) and mode in ({})".format(
                str(self.strategy_ids).replace("[", "").replace("]", ""), str(list(self.period.months)).replace('[','').replace(']','')))
            cursor.executemany("insert into turnover_backtest values {}".format(values), res)

    def _setAmFee(self):
        init_account = [[strategy_config['strategy_id'], self.init_account_date, 0,0,0,0,0,0,0,0,0,0,0] for strategy_config in
                        self.strategy_configs]
        self.am_fee.extend(init_account)

    @func_timer
    def run(self):
        pre_position = initPandasDataFrame(position)
        pre_asset = self._setAsset()
        pre_account = self._setAccount()
        self._setAmFee()
        today_asset = pre_asset
        need_cash = pd.DataFrame(columns=['strategy_id', 'trade_date', 'need_cash'])
        # 第一天，如果是对冲策略，划拨资金，否则不变
        pre_account = self.futureManager.reset_account_first_trade_date(pre_account, self.riskManager.futureConf, self.trade_dates[0])
        today_account = pre_account
        if self.risk_configs is None or self.risk_configs.__len__() == 0:
            for trade_date in self.trade_dates:
                adjust_target_position = self.target_position.query('trade_date=="{}"'.format(trade_date))
                trade = self.targetOrder.run(trade_date, adjust_target_position, pre_position, today_asset,  today_account)
                pre_position, pre_account, pre_asset, need_cash, today_account, today_asset = self.clearSettle.runClearSettle(trade_date,
                                                   trade, pre_position, today_account, today_asset)
        else:
            for trade_date in self.trade_dates:
                print(trade_date)
                # if trade_date == '20161230':
                #     print('debug')
                adjust_target_position = self.riskManager.run(trade_date,
                                                              preAsset=pre_asset,
                                                              df_commission=need_cash,
                                                              today_asset=today_asset,
                                                              today_account=today_account)
                trade = self.targetOrder.run(trade_date, adjust_target_position, pre_position, today_asset, today_account)
                pre_position, pre_account, pre_asset, need_cash, today_account, today_asset = self.clearSettle.runClearSettle(trade_date,
                                                      trade, pre_position, today_account, today_asset)
                self.futureManager.moveCash(today_account)
        self.performance = self.clearSettle.performance(self.asset, self.performance_configs, am_config=self.am_configs)
        self.asset.extend(today_asset.values.tolist())
        self.account.extend(today_account.values.tolist())
        self.turnover = PerformanceIndex.turnover(self.strategy_ids, self.env, self.init_account_date, self.trade_dates[-1], backtest=True)

if __name__ == '__main__':
    backtest = BackTest(['test',
                        # 'S-L-4|LastPrice|CLOSE|RISK-38|100M',
                        # 'S-L-4|LastPrice|CLOSE|RISK-171',
                         ], '20100501', '20110523')
    print('M-L|LastPrice|CLOSE|RISK-175-2|100M|l')
    backtest.run()
    backtest.saveResult2DB()
    backtest.period_performance()


