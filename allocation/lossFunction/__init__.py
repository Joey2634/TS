from allocation.lossFunction.AverageReturn import AverageReturn
from allocation.lossFunction.CumulativeReturn import CumulativeReturn
from allocation.lossFunction.InformationRatio import InformationRatio
from allocation.lossFunction.MaxDiversification import MaxDiversification
from allocation.lossFunction.RiskParity import RiskParity
from allocation.lossFunction.SharpeRatio import SharpeRatio
from allocation.lossFunction.SortinoRatio import SortinoRatio


# facotry to get loss function
def getLossFunction(strategy_template, paras):
    if strategy_template == 'SortinoRatio':
        return SortinoRatio(paras)
    if strategy_template == 'SharpeRatio':
        return SharpeRatio(paras)
    if strategy_template == 'CumulativeReturn':
        return CumulativeReturn(paras)
    if strategy_template == 'AverageReturn':
        return AverageReturn(paras)
    if strategy_template == 'RiskParity':
        return RiskParity(paras)
    if strategy_template == 'MaxDiversification':
        return MaxDiversification(paras)
    if strategy_template == 'InformationRatio':
        return InformationRatio(paras)
    raise ValueError("invalid strategy_template: ", strategy_template)
