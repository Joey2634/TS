from allocation.SimpleAverage import SimpleAverage
from allocation.weightedByCondition.LastPrice import LastPrice
from allocation.weightedByCondition.MarketValue import MarketValue
from allocation.weightedByCondition.PE import PE
from allocation.weightedByCondition.FreeMarketValue import FreeMarketValue
from allocation.weightedByCondition.Amount import Amount
def WeightedBy(strategy_template: str):
    if strategy_template == 'LastPrice':
        return LastPrice()
    if strategy_template == 'MarketValue':
        return MarketValue()
    if strategy_template == 'PE':
        return PE()
    if strategy_template == 'FreeMarketValue':
        return FreeMarketValue()
    if strategy_template == 'Amount':
        return Amount()