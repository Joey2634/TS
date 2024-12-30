import multiprocessing
import numpy as np
import pandas as pd
from allocation import setAllocationResult, setAllocationData
from configs.tableConfig import initPandasDataFrame, target_position

idx = pd.IndexSlice
class Allocation:
    def __init__(self, strategy_configs, allocation_configs, trade_dates, security_pool, market_quotes,env='dev', mode='backtest'):
        self.strategy_configs = strategy_configs
        self.allocation_configs = allocation_configs
        self.trade_dates = trade_dates
        self.security_pool = security_pool
        self.market_quotes = market_quotes
        self.env = env
        self.mode = mode

    def run(self):
        # pool = multiprocessing.Pool()
        # rows = []
        # for strategy_config in self.strategy_configs:
        #         rows.append(pool.apply_async(self._AllocationBacktest, (strategy_config['strategy_id'],
        #                                                                 strategy_config['selection_id'],
        #                                                                 strategy_config['allocation_id'])))
        # pool.close()
        # pool.join()
        weights = np.array([])
        weights.shape = (0, 5)
        for strategy_config in self.strategy_configs:
            result = self._AllocationBacktest(strategy_config['strategy_id'], strategy_config['selection_id'],
                                                                            strategy_config['allocation_id'])
            weights = np.vstack((weights, result))
        return initPandasDataFrame(target_position, weights)

    @classmethod
    def updateWindInfoTables(self, result, security_pool, allocation_configs, mode='backtest'):
        for name in allocation_configs.keys():
            table_dict = setAllocationData(name, mode)
            for table, item in table_dict.items():
                if table != 'liveMarketInfo' and table != '':
                    result[table]['codes'].update(security_pool)
                    result[table]['fields'].update(item)

    def _AllocationBacktest(self, strategy_id, selection_id, allocation_id):
        # 初始化资产配置模型
        print(strategy_id)
        allocationStrategy = setAllocationResult(self.allocation_configs[allocation_id]['allocation_strategy'])
        table = setAllocationData(allocation_id, self.mode)
        pool = list(set.union(*map(set, self.security_pool[selection_id].values()))) if self.security_pool[selection_id] else []
        if self.mode == 'live' and allocation_id == 'LastPrice':
            data = self.market_quotes[list(table.keys())[0]].loc[pool]
        else:
            data = pd.DataFrame()
            for tab in table.keys():
                if tab != '' and not self.market_quotes[tab].empty:
                    data = pd.concat([self.market_quotes[tab].loc[idx[:, pool],],data])

        # 计算资产配置权重
        result = allocationStrategy.setWeights(strategy_id, self.allocation_configs[allocation_id],
                                               self.trade_dates, self.security_pool[selection_id], data, self.mode)
        return result