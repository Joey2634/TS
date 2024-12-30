from itertools import chain
import pandas as pd
from utils.Date import getTradeSectionDates, getTradeDates

idx = pd.IndexSlice
class MarketValue:

    def run(self, trade_dates, pool, data, sample_size, mode='backtest'):
        weight = [list(map(lambda x, y: [x, y], [day for i in range(len(pool[day]))], pool[day])) for day in
                  trade_dates]
        weight = pd.DataFrame(list(chain.from_iterable(weight)), columns=['TRADE_DT', 'S_INFO_WINDCODE'])
        test_day = getTradeSectionDates(trade_dates[0], -2)[0]
        tradeDays = getTradeDates(test_day, trade_dates[-1])
        price = data.loc[idx[tradeDays[:-1], :], ][['S_DQ_MV']]
        price = price.reset_index()
        price['TRADE_DT'] = list(map(lambda x: tradeDays[tradeDays.index(x)+1], price['TRADE_DT']))
        weight = pd.merge(weight, price, how='left', on=['TRADE_DT', 'S_INFO_WINDCODE'])
        weight['sum'] = weight.groupby('TRADE_DT')['S_DQ_MV'].transform('sum')
        weight['S_DQ_MV'] = weight['S_DQ_MV'] / weight['sum']
        weight.rename(
            columns={'TRADE_DT': 'trade_date', 'S_DQ_MV': 'target_ratio', 'S_INFO_WINDCODE': 'windcode'},
            inplace=True)
        return weight.loc[:, ['trade_date', 'windcode', 'target_ratio']]
