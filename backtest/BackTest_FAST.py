import multiprocessing
from collections import defaultdict
from typing import List
from collections import defaultdict
from rediscluster import RedisCluster
import os
import _pickle
from utils.AiData import which_table
from allocation.Allocation import Allocation
from clearSettle.Performance import Performance
from configs.Database import mysql, SHARE
from utils.Date import getTradeSectionDates, getTradeDates
from utils.AiData import getFuturesContractMultiplierDB, getMarginRate, getWindData, daily_data
from utils.Decorator import func_timer
from itertools import product
from configs.tableConfig import *
from configs.Redis import redis_client_dict

idx = pd.IndexSlice
data_path = '../testCase/BackTest/'
class BackTest:

    def __init__(self, selection_ids, allocation_ids, trade_prices, start_date, end_date, env='dev', filename='BackTestFast'):
        self.selection_ids = selection_ids
        self.trade_prices = trade_prices
        self.allocation_ids = allocation_ids
        self._getStrategyConfig()
        self.trade_dates = getTradeDates(start_date, end_date)
        self.env = env
        with mysql(env) as self.cursor:
            self.allocation_configs = self._getConfig('allocation_config', 'allocation_id', allocation_ids)
        self.position = []
        self.trade = []
        self.performance_dat = pd.DataFrame()
        self._setSecurityPool()
        self._setWindInfo()
        self.setTargetPosition()
        with mysql(SHARE) as self.cursor:
            self.fee_rate = self._loadFeeRate()
        self.index_list = ['TOTAL_RETURNS', 'ANNAUL_RETURN', 'AVG_YEAR_RETURN', 'SHARPE_RATIO', 'SORTINO_RATIO',
                           'MAX_DRAWDOWN',
                           'LONGEST_MAX_DRAWDOWN_DURATION', 'MAX_DRAWDOWN_5BD', 'MAX_DRAWDOWN_20BD', 'AVG_DAILY_RETURN',
                           'STD_DEV_DAILY_RETURN']
        self.rfr = 0.0001
        self.filename = filename

    def _getStrategyConfig(self):
        configs = list(product(*[self.selection_ids, self.allocation_ids, self.trade_prices]))
        self.strategy_ids = list(map(lambda x: '|'.join(x), configs))
        configs = list(map(lambda x: dict(zip(['selection_id', 'allocation_id','trade_price'],x)),configs))
        self.strategy_configs = list(map(lambda x, y: dict(x, **{'strategy_id': y}), configs, self.strategy_ids))

    @func_timer
    def _setSecurityPool(self):
        self.security_pool = {}
        self.security_list = set()
        name = 'ai-investment-manager|security_pool'
        selection_ids: List[str] = list(set(config['selection_id'] for config in self.strategy_configs))
        redis_cli = RedisCluster(startup_nodes=redis_client_dict[self.env], password='citics')
        selection_id: str
        for selection_id in selection_ids:
            self.security_pool[selection_id] = eval(redis_cli.hget(name, selection_id))
            removed_date: List[str] = list(filter(lambda x: x not in self.trade_dates, list(self.security_pool[selection_id])))
            for date in removed_date:
                self.security_pool[selection_id].pop(date)
            for value in self.security_pool[selection_id].values():
                self.security_list.update(value)
        if self.security_list.__contains__('CASH'):
            self.security_list.remove('CASH')

    @func_timer
    def setTargetPosition(self):
        # table_name = 'AShareEODPrices'
        allocation = Allocation(self.strategy_configs, self.allocation_configs, self.trade_dates, self.security_pool,self.windInfo)
        self.target_position = allocation.run()
        print(self.target_position)

    @func_timer
    def _getConfig(self, table, key, ids):
        result = {}
        # ids = set(config[key] for config in self.strategy_configs)
        if 'NONE' in ids:
            ids.remove('NONE')
        sql = "SELECT * FROM " + table + " where " + key
        if len(ids) > 1:
            sql = sql + " in {0}".format(tuple(ids))
        elif len(ids) == 1:
            sql = sql + " = '{0}'".format(ids[0])
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
        table_name = which_table(list(self.security_list)[0])
        Allocation.updateWindInfoTables(windInfoDict, security_pool=self.security_list, allocation_configs=self.allocation_configs)
        windInfoDict[table_name]['fields'].update(set(self.trade_prices+['TRADE_DT', 'S_INFO_WINDCODE','S_DQ_CLOSE','S_DQ_PRECLOSE']))
        windInfoDict[table_name]['codes'].update(self.security_list)
        # 根据各个模块搜集的信息获取数据
        self.windInfo = {}
        sample_size = max(
            set(int(self.allocation_configs[config]['sample_size']) for config in self.allocation_configs)) + 1
        market_quotes_start_date = getTradeSectionDates(self.trade_dates[0], -sample_size)[0]
        for table, info in windInfoDict.items():
            self.windInfo[table] = getWindData(
                table=table, code_list=info['codes'], start_date=market_quotes_start_date,
                end_date=self.trade_dates[-1], fields=info['fields'])
            if table in daily_data:
                self.windInfo[table].set_index(['TRADE_DT', 'S_INFO_WINDCODE'], inplace=True)
            elif table == 'CFuturesContPro':
                self.windInfo['multiplier'] = getFuturesContractMultiplierDB(self.windInfo, self.trade_dates[0],self.trade_dates[-1])
            elif table == 'CFuturesmarginratio':
                self.windInfo['margin_ratio'] = getMarginRate(self.windInfo, self.trade_dates[0], self.trade_dates[-1])


    def _loadFeeRate(self, business_types=['rootNet']):
        """
        加载费率信息
        :param total_security_list:
        :param strategy_configs:
        :return:
        """
        # business_types = set([config['business_type'] for config in strategy_configs])
        sql = "select business_type,windcode,fee_type,fee_rate from trading_fee_rate where business_type"
        if len(business_types) > 1:
            sql = sql + " in {0}".format(tuple(business_types))
        elif len(business_types) == 1:
            sql = sql + " = '{0}'".format(business_types.pop())
        else:
            exit("Error: No Business Type")
        sql += " and windcode"
        if len(self.security_list) > 1:
            sql = sql + " in {0}".format(tuple(self.security_list))
        elif len(self.security_list) == 1:
            sql = sql + " = '{0}'".format(tuple(self.security_list)[0])
        else:
            exit("Error: No security")
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        df = pd.DataFrame(data=list(data), columns=['business_type', 'windcode', 'fee_type', 'fee_rate'])
        df['fee_rate'] = df['fee_rate'].astype('float')
        df['BS'] = df['fee_type'].map({'B': 1, 'S': -1})
        return df

    @func_timer
    def run(self):
        table_name = which_table(list(self.security_list)[0])
        pool = multiprocessing.Pool()
        row = []
        self.market_quotes = self.windInfo[table_name].reset_index()
        self.market_quotes['PCTCHANGE'] = self.market_quotes['S_DQ_CLOSE']/self.market_quotes['S_DQ_PRECLOSE'] - 1
        self.codes_pct = self.market_quotes.pivot('TRADE_DT', 'S_INFO_WINDCODE','PCTCHANGE').fillna(0).sort_index(axis=0)
        for config in self.strategy_configs:
            row.append(pool.apply_async(self.performance, (config, self.target_position[self.target_position['strategy_id'] == config['strategy_id']])))
        pool.close()
        pool.join()
        for res in row:
            self.performance_dat = pd.concat([self.performance_dat, res.get()])
        # for config in self.strategy_configs:
        #     strategy_id = config['strategy_id']
        #     self.performance_dat.loc[strategy_id, 'selection_id'] = config['selection_id']
        #     self.performance_dat.loc[strategy_id, 'allocation_id'] = config['allocation_id']
        #     self.performance_dat.loc[strategy_id, 'trade_price'] = config['trade_price']
        self.performance_dat['benchmark_id'] = 'strategy'
        # self.performance_dat.to_csv(data_path+self.filename+'.csv', mode='a+', index=False)
        self.saveResult2DB()
        print(self.performance_dat)

    def saveResult2DB(self, condition=""):
        '''
        存入数据库
        :param tables: 要存库的表名
        :param condition: 筛选条件
        :param delete: 是否删除重复数据
        :return:
        '''
        # performance_df = pd.DataFrame(self.performance_dat, columns=performance['columns'])
        performance_df = self.performance_dat.query(condition+"and benchmark_id=='strategy'") if condition else self.performance_dat
        if performance_df.empty:
            print("没有满足条件的策略")
            return
        with mysql(self.env, commit=True) as self.cursor:
                values = str(('%s',) * len(performance_df.values.tolist()[0])).replace("'", "")
                self.cursor.execute("delete from performance_backtest where strategy_id in ({})".format(str(self.strategy_ids).replace("[","").replace("]","").strip(",")))
                self.cursor.executemany("insert into performance_backtest values {}".format(values), performance_df.values.tolist())

    @func_timer
    def performance(self, config, position):
        position = position.pivot('trade_date', 'windcode', 'target_ratio')
        codes = position.columns.tolist()
        weight = pd.DataFrame(index=self.trade_dates, columns=codes)
        weight = weight.add(position, fill_value=0).fillna(0)
        codes_earn = self.market_quotes.loc[:, ['TRADE_DT', 'S_INFO_WINDCODE']]
        codes_earn['EARN'] = self.market_quotes['S_DQ_CLOSE'] / self.market_quotes[config['trade_price']] - 1
        codes_earn = codes_earn.pivot('TRADE_DT', 'S_INFO_WINDCODE', 'EARN').fillna(0).sort_index(axis=0)
        sweight = weight.shift(periods=1, axis=0).fillna(0)
        det = np.array(weight.diff().fillna(0))
        test = np.multiply(np.array(sweight), np.array(self.codes_pct.loc[self.trade_dates, codes]))
        dshouyi = np.multiply(det, np.array(codes_earn.loc[self.trade_dates, codes]))
        feerate = self.fee_rate.pivot('fee_type', 'windcode', 'fee_rate')[codes]
        fee = pd.DataFrame(columns=codes, index=self.trade_dates)
        fee_B = np.array(fee.apply(lambda x: feerate.loc['B'], axis=1))
        fee_S = np.array(fee.apply(lambda x: feerate.loc['S'], axis=1))
        fe = (np.multiply(det, fee_B)+np.multiply(abs(det), fee_B)-np.multiply(det, fee_S)+np.multiply(abs(det), fee_S)) * 0.5
        worth = test.sum(axis=1) + dshouyi.sum(axis=1) - fe.sum(axis=1)
        performanc_kpi = Performance(config['strategy_id'], [], [])
        performance_data = performanc_kpi.getPerformanceAssessment(self.rfr,
                                                                   pd.DataFrame(data=list(zip(self.trade_dates, worth)), columns=['date',config['strategy_id']]))
        return performance_data

if __name__ == '__main__':
    selection_ids = ['S-L-30']
    allocation_ids = ['MaxDiversification40']
    trade_prices = ['AVERAGE']
    backtest = BackTest(selection_ids,allocation_ids,trade_prices, '20150101', '20210120')
    # 'RiskParity','MaxDiversification70','MaxDiversification120',
    #                       'MaxDiversification100','MaxDiversification'
    #  'PE'MarketValueLastPrice
    # 'S_DQ_CLOSE','S_DQ_OPEN','AVERAGE'
    backtest.run()
