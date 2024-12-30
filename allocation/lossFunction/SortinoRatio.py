from .lossFunction import *


class SortinoRatio(lossFunction):

    def get(self):
        below = [(self.paras[RET][x]) ** 2 for x in range(len(self.paras[RET])) if self.paras[RET][x] < 0]
        sortino = sum(below) / len(below)
        return sortino
