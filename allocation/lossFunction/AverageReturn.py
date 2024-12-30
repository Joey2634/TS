import numpy as np
from .lossFunction import *


class AverageReturn(lossFunction):

    def get(self):
        return np.mean(self.paras[RET])
