import pandas as pd
from clearSettle.assetManagement.AssetManagementFee import AssetManagementFee
from utils.AiData import loadCommissionRate


class AssetManagementFeeBacktest(AssetManagementFee):
    def __init__(self, env, am_configs, assetFee, asset):
        super().__init__(env, am_configs)
        self.assetFeeList = assetFee  # 回测模式下数据库am_fee表数据,list可以传出
        self.assetFee = pd.DataFrame()
        self.asset = asset  # 历史asset数据 计算业绩报酬使用
        self.preAssetFee = pd.DataFrame()  # 记录昨日资管费用
        self.commissionRate = loadCommissionRate(list(self.am_configs.keys()), env=env)


    def run(self, trade_date, trade, asset, cash):
        self.setTradeDate(trade_date)
        self.need_cash = pd.DataFrame(columns=['strategy_id', 'trade_date', 'need_cash'])  # 记录需要增加的现金
        if not set(asset['strategy_id'].values.tolist()) & set(self.am_configs.keys()):
            return
        assetFee = self.calCommission(trade)
        # 计算管理费\托管费\业绩报酬
        self.calAssetFee(asset, assetFee)
        # 计算业绩报酬
        assetDF = asset.drop(columns='cash')
        assetDF = pd.merge(assetDF, cash)
        self._calAllFee(assetDF)
        # 每日账单存库
        self.saveToAssetFee()

    def saveToAssetFee(self):
        '''
        每日账单存库
        '''
        assetFee = self.getAmFee()
        self.assetFee = self.assetFee.append(assetFee)
        self.assetFeeList.extend(assetFee.values.tolist())
        self.preAssetFee = self.nowAssetFee


