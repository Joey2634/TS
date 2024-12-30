import numpy as np
from .weightedByCondition import WeightedBy

class WeightedAverage:

    def updateWeights(self, windcodes, trade_date):
        pass

    def setWeights(self, strategy_id, paras, trade_dates, pool, data, mode='backtest'):
        if data.empty: return np.empty(shape=(0, 5))
        weightedby = WeightedBy(paras['factor'])
        weights = weightedby.run(trade_dates, pool, data, int(paras['sample_size']), mode)
        weights['strategy_id'] = strategy_id
        weights['LS'] = 1
        weights = weights[['strategy_id', 'trade_date', 'windcode', 'LS', 'target_ratio']]
        return np.array(weights)
