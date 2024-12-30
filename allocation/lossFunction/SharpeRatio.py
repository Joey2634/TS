from .lossFunction import *
import numpy as np

class SharpeRatio(lossFunction):

    def get(self):
        w = np.asmatrix(self.paras['weight'])
        ls = (w * self.paras['cov1'] * w.T)[0, 0]  # 计算组合风险
        sig_p = np.sqrt(ls)
        mean = self.paras[RET].mean()
        return (mean - self.paras[RRR]) / sig_p
