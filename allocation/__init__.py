from .MinimizeLossFunction import MinimizeLossFunction
from .WeightedAverage import WeightedAverage
from .SimpleAverage import SimpleAverage

def setAllocationResult(allocation_strategy):
    if allocation_strategy == 'MinimizeLossFunction':
        return MinimizeLossFunction()
    if allocation_strategy == 'WeightedAverage':
        return WeightedAverage()
    if allocation_strategy == 'SimpleAverage':
        return SimpleAverage()
    raise ValueError("invalid strategy_template: ", allocation_strategy)

def setAllocationData(factor, mode):
    if factor == 'MarketValue':
        return {'AShareEODDerivativeIndicator': {'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_MV'}}
    if factor == 'FreeMarketValue':
        return {'AShareEODDerivativeIndicator': {'TRADE_DT', 'S_INFO_WINDCODE', 'FREE_SHARES_TODAY','S_DQ_CLOSE_TODAY'}}
    if factor == 'PE':
        return {'AShareEODDerivativeIndicator': {'TRADE_DT', 'S_INFO_WINDCODE', 'S_VAL_PE'}}
    if factor == 'Amount':
        return {'AShareEODPrices': {'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_AMOUNT'},
                    'ChinaClosedFundEODPrice':{'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_AMOUNT'},
                    'HKshareEODPrices':{'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_AMOUNT'}}
    if factor == 'LastPrice':
        if mode == 'backtest':
            return {'AShareEODPrices': {'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_OPEN'},
                    'ChinaClosedFundEODPrice':{'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_OPEN'},
                    'HKshareEODPrices':{'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_OPEN'}}
        else:
            return {'liveMarketInfo': {'windcode', 'lastPrice'}}
    if factor == 'SimpleAverage':
        return {'': {}}
    # if factor == 'RiskParity':
    return {'AShareEODPrices': {'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_PRECLOSE','S_DQ_CLOSE'},
            'ChinaClosedFundEODPrice':{'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_PRECLOSE','S_DQ_CLOSE'},
            'HKshareEODPrices':{'TRADE_DT', 'S_INFO_WINDCODE', 'S_DQ_PRECLOSE','S_DQ_CLOSE'}}
