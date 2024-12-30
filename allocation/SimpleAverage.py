import pandas as pd
import numpy as np
from itertools import chain
idx = pd.IndexSlice

class SimpleAverage:

    def updateWeights(self, windcodes, trade_date):
        pass

    def setWeights(self, strategy_id, paras, trade_dates, pool, data, mode='backtest'):
        weight = [list(map(lambda x, y: [x, y], [day for i in range(len(pool[day]))], pool[day])) for day in
                  trade_dates] if pool else []
        weight = pd.DataFrame(list((chain.from_iterable(weight))), columns=['TRADE_DT', 'S_INFO_WINDCODE'])
        weight['target_ratio'] = 1
        weight['sum_price'] = weight.groupby('TRADE_DT')['target_ratio'].transform('sum')
        weight['target_ratio'] = weight['target_ratio'] / weight['sum_price']
        weight.rename(columns={'TRADE_DT': 'trade_date', 'S_INFO_WINDCODE': 'windcode'}, inplace=True)
        weight['strategy_id'] = strategy_id
        weight['LS'] = 1
        weight = weight[['strategy_id', 'trade_date', 'windcode', 'LS', 'target_ratio']]
        return np.array(weight)
