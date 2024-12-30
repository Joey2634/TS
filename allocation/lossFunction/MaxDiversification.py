import numpy as np
from .lossFunction import *


class MaxDiversification(lossFunction):

    def get(self):
        """
        最大多元化对应的方法函数
        :param rate_train: 训练的收益率表
        :return: 权重，是否成功运算flag，协方差矩阵
        """
        w = np.asmatrix(self.paras['weight'])
        ls = np.dot(np.dot(w, self.paras['cov1']), w.T)[0,0]  # 计算组合风险
        sig_p = np.sqrt(ls)
        risk = (np.dot(np.array(self.paras['weight']), self.paras['sigma']) / sig_p)
        return risk
