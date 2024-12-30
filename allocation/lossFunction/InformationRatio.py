import numpy as np

from .lossFunction import *


class InformationRatio(lossFunction):

    def get(self):
        excess_ret = self.paras[RET] - self.paras[BENCHMARK]
        std = excess_ret.std()
        if std == 0:
            return 0
        mean = excess_ret.mean()
        return mean / std
