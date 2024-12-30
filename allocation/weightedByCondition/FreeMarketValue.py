from itertools import chain
import pandas as pd

from utils.Date import getTradeSectionDates, getTradeDates

idx = pd.IndexSlice
class FreeMarketValue:

    def run(self, trade_dates, pool, data, sample_size,mode='backtest'):
        weight = [list(map(lambda x, y: [x, y], [day for i in range(len(pool[day]))], pool[day])) for day in
                  trade_dates]
        weight = pd.DataFrame(list(chain.from_iterable(weight)), columns=['TRADE_DT', 'S_INFO_WINDCODE'])
        test_day = getTradeSectionDates(trade_dates[0], -2)[0]
        tradeDays = getTradeDates(test_day, trade_dates[-1])
        price = data.loc[idx[tradeDays[:-1], :], ][['FREE_SHARES_TODAY','S_DQ_CLOSE_TODAY']]
        price['FreeMV'] = price['FREE_SHARES_TODAY'] *price['S_DQ_CLOSE_TODAY']
        price = price.reset_index()
        price['TRADE_DT'] = list(map(lambda x: tradeDays[tradeDays.index(x)+1], price['TRADE_DT']))
        price = price.dropna(axis=0,subset=['S_DQ_CLOSE_TODAY'])
        weight = pd.merge(weight, price, how='left', on=['TRADE_DT', 'S_INFO_WINDCODE'])
        weight['sum_price'] = weight.groupby('TRADE_DT')['FreeMV'].transform('sum')
        weight['FreeMV'] = weight['FreeMV'] / weight['sum_price']
        weight.rename(
            columns={'TRADE_DT': 'trade_date', 'FreeMV': 'target_ratio', 'S_INFO_WINDCODE': 'windcode'},
            inplace=True)
        return weight.loc[:, ['trade_date', 'windcode', 'target_ratio']]
