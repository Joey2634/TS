import pandas as pd
import numpy as np
from itertools import chain
from utils.Date import getTradeSectionDates, getTradeDates
idx = pd.IndexSlice
class Amount:

    def run(self, trade_dates, pool, data, sample_size,mode='backtest'):
        # if mode == 'live':
        #     data['TRADE_DT'] = trade_dates[0]
        #     data = data.reset_index().rename(columns={'windcode': 'S_INFO_WINDCODE', 'lastPrice': 'S_DQ_OPEN'})
        #     data.set_index(['TRADE_DT', 'S_INFO_WINDCODE'], inplace=True)
        weight = [list(map(lambda x, y:[x, y], [day for i in range(len(pool[day]))], pool[day])) for day in trade_dates]
        weight = pd.DataFrame(list(chain.from_iterable(weight)), columns=['TRADE_DT', 'S_INFO_WINDCODE'])
        test_day = getTradeSectionDates(trade_dates[0], -sample_size-1)[0]
        self.tradeDays = getTradeDates(test_day, trade_dates[-1])
        self.size = sample_size
        amount = data.loc[idx[self.tradeDays, :], ][['S_DQ_AMOUNT']]
        self.data = data
        # amount['amount'] = amount.apply(self.cacu_amount, axis=1)
        amount['amount'] = list(map(self.cacu_amount, amount.index))
        amount = amount.reset_index()
        weight = pd.merge(weight, amount, how='left', on=['TRADE_DT', 'S_INFO_WINDCODE']).dropna()
        weight['sum_amount'] = weight.groupby('TRADE_DT')['amount'].transform('sum')
        weight['amount'] = weight['amount'] / weight['sum_amount']
        weight.rename(columns={'TRADE_DT': 'trade_date', 'amount': 'target_ratio', 'S_INFO_WINDCODE': 'windcode'}, inplace=True)
        return weight.loc[:, ['trade_date', 'windcode', 'target_ratio']]

    def cacu_amount(self, index):
        if self.tradeDays.index(index[0]) >= self.size:
            days = self.tradeDays[self.tradeDays.index(index[0]) - self.size: self.tradeDays.index(index[0])]
            return np.mean(self.data.loc[idx[days,index[1]],:]['S_DQ_AMOUNT'])
        else:
            return 0