import numpy as np

from .lossFunction import *


class CumulativeReturn(lossFunction):

    def get(self):
        return np.prod(np.array(self.paras[RET]) + 1.0)
