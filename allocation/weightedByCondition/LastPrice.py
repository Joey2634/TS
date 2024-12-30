import pandas as pd
from itertools import chain
idx = pd.IndexSlice
class LastPrice:

    def run(self, trade_dates, pool, data, sample_size,mode='backtest'):
        if mode == 'live':
            data['TRADE_DT'] = trade_dates[0]
            data = data.reset_index().rename(columns={'windcode': 'S_INFO_WINDCODE', 'lastPrice': 'S_DQ_OPEN'})
            data.set_index(['TRADE_DT', 'S_INFO_WINDCODE'], inplace=True)
        weight = [list(map(lambda x, y:[x, y], [day for i in range(len(pool[day]))], pool[day])) for day in trade_dates]
        weight = pd.DataFrame(list(chain.from_iterable(weight)), columns=['TRADE_DT', 'S_INFO_WINDCODE'])
        price = data.loc[idx[trade_dates, :], ][['S_DQ_OPEN']]
        price = price.reset_index()
        weight = pd.merge(weight, price, how='left', on=['TRADE_DT', 'S_INFO_WINDCODE']).dropna()
        weight['sum_price'] = weight.groupby('TRADE_DT')['S_DQ_OPEN'].transform('sum')
        weight['S_DQ_OPEN'] = weight['S_DQ_OPEN'] / weight['sum_price']
        weight.rename(columns={'TRADE_DT': 'trade_date', 'S_DQ_OPEN': 'target_ratio', 'S_INFO_WINDCODE': 'windcode'}, inplace=True)
        return weight.loc[:, ['trade_date', 'windcode', 'target_ratio']]
