import multiprocessing

import numpy as np
import copy
import pandas as pd
from scipy.optimize import minimize
from utils.Date import getTradeSectionDates
from .lossFunction import getLossFunction
idx = pd.IndexSlice

class MinimizeLossFunction:

    def updateWeights(self, strategy_ids, trade_date):
        pass

    def setWeights(self, strategy_id, paras, trade_dates, pool, data, mode='backtest'):
        multpool = multiprocessing.Pool()
        rows = []
        for trade_day in trade_dates:
            rows.append(multpool.apply_async(self.LossFunctionReturn, (strategy_id, paras, trade_day,
                                                                       data.loc[idx[:, pool[trade_day]], ])))
        multpool.close()
        multpool.join()
        weights = np.array([])
        weights.shape = (0, 5)
        for res in rows:
            weights = np.vstack((weights, res.get()))
        return weights

    def LossFunctionReturn(self, strategy_id, para, day, data):
        if data.empty: return np.empty(shape=(0, 5))
        rate = self.get_data(-int(para['sample_size']), day, data)
        codes = list(rate.columns)
        V1 = np.asmatrix(self._find_cov(rate))
        sigma = self._find_sigma(rate)
        rate_train = copy.deepcopy(rate)
        rate_train = rate_train.cumprod()
        V2 = np.asmatrix(self._find_cov(rate_train))
        lenth = len(sigma)
        w0 = (np.ones(lenth) / lenth).tolist()
        w1 = w0.copy()
        bonds = ([(0, 1) for i in range(lenth)])
        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},
                {'type': 'ineq', 'fun': lambda x: x})
        rrr = float(para.get('rrr', 0))
        res = minimize(self._LossFunction, w0, args=[para['loss_function'], w1, V1, V2, sigma, rate, rrr], method='SLSQP',
                       constraints=cons, bounds=bonds,
                       options={'disp': True, 'eps': float(para['epsilon']), 'ftol': float(para['ftol']),
                                'maxiter': 600})
        print(day, lenth, res.success)
        if res.success:
            weights = pd.DataFrame(data=list(zip(codes, res.x)), columns=['windcode', 'target_ratio'])
            weights['trade_date'] = day
            weights['strategy_id'] = strategy_id
            weights['LS'] = 1
            weights = weights[['strategy_id', 'trade_date', 'windcode', 'LS', 'target_ratio']]
            return np.array(weights)
        else:
            print('历史回测数据存在错误')
            return np.empty(shape=(0, 5))

    def _LossFunction(self, x, pars):
        paras = {}
        paras['weight'] = x
        paras['string'] = pars[0]
        paras['weight0'] = pars[1]
        paras['cov1'] = pars[2]
        paras['cov2'] = pars[3]
        paras['sigma'] = pars[4]
        paras['ret'] = np.dot(pars[5] - 1, np.array(x))
        paras['benchmark'] = np.dot(pars[5] - 1, np.array(pars[1]))
        paras['rrr'] = pars[6]
        Loss = getLossFunction(paras['string'], paras)
        return -Loss.get()

    def _find_cov(self, rate):
        """
        根据收益率得到收益率的协方差矩阵
        :param rate: 收益率DataFrame
        :return: 协方差矩阵
        """
        c = rate.columns.tolist()
        g = pd.DataFrame(0, index=c, columns=c)
        for i in c:
            for j in c:
                if not g.loc[i, j]:
                    ls = np.cov(rate[[i, j]].dropna().T)[0, 1]
                    g.loc[i, j] = ls
                    g.loc[j, i] = ls
        return g

    def _find_sigma(self, rate):
        """
        根据收益率得到波动率
        :param rate: 收益率DataFrame
        :return: 波动率数组
        """
        sigma = []
        for i in rate:
            sigma.append(rate[i].std())
        return np.array(sigma)

    def get_data(self, sample_size, day, data):
        data['PCTCHANGE'] = data['S_DQ_CLOSE'] / data['S_DQ_PRECLOSE'] - 1
        day_end = getTradeSectionDates(day, -2)[0]
        days = getTradeSectionDates(day_end, sample_size)
        data = data.loc[idx[days, :],][['PCTCHANGE']].reset_index()
        data = data.pivot('TRADE_DT', 'S_INFO_WINDCODE', 'PCTCHANGE').fillna(0).sort_index(axis=0)
        data.iloc[0, ] = 0
        return data.add(1)
