import numpy as np
from .lossFunction import *


class RiskParity(lossFunction):

    def get(self):
        """
        风险平价对应的方法函数
        :param rate_train: 训练的收益率表
        :return: 权重，是否成功运算flag，协方差矩阵
        """
        w = np.asmatrix(self.paras['weight'])
        ls = (w * self.paras['cov2'] * w.T)[0, 0]  # 计算组合风险
        sig_p = np.sqrt(ls)
        risk_target = np.asmatrix(np.multiply(sig_p, self.paras['weight0']))
        asset_RC = self._calculate_risk_contribution(sig_p)
        J = sum(np.square(asset_RC - risk_target.T))[0, 0]
        return -J

    def _calculate_risk_contribution(self, sigma):
        """
        计算单个资产对总体风险贡献度的函数
        :param sigma: 波动率
        :return: 风险贡献的值
        """
        w = np.asmatrix(self.paras['weight'])
        MRC = self.paras['cov2'] * w.T / sigma
        RC = np.multiply(MRC, w.T)
        return RC
