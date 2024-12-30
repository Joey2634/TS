# -*- coding: utf-8 -*-
"""
Created on Sat Dec 19 11:08:58 2020

@author: jhz03
"""

# 导入回测的主要数据
import statsmodels.api as sm
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns

global Data_Dir
# 设定数据路径！！！
# Data_Dir = 'D:\\python\\Data\\'
Data_Dir = ''


# 导入因子模型
def loadBenchMark():
    # 实际应用，换成CSI300指数的月度交易数据
    df = pd.read_csv(Data_Dir + 'fivefactor_monthly.csv')
    df.index = [str(x)[:4] + '-' + str(x)[4:7] for x in df.trdmn]
    df.index.name = 'Trdmnt'
    df['Bench_Ret'] = df['mkt_rf']

    return df[['Bench_Ret']]


# 股票观测数据过滤
def stockFilter(df):
    df_pivot = df.pivot(index='Trdmnt', columns='Stkcd', values='Mretnd')
    df_pivot = df_pivot.rolling(window=12).count()
    df_pivot = df_pivot.unstack().reset_index().rename(columns={0: 'TrdMonNum'})
    df = pd.merge(df, df_pivot, on=['Stkcd', 'Trdmnt'], how='left')
    df = df[df.TrdMonNum >= 11]
    del df['TrdMonNum']

    return df


# 导入交易数据
def loadMainTrdData():
    df = pd.read_csv(Data_Dir + 'TRD_Mnth.csv')
    df['Stkcd'] = [str(x).zfill(6) for x in df.Stkcd]
    df['isNormal'] = [x[0] in ['0', '3', '6'] for x in df.Stkcd]
    df = df[df.isNormal]
    df = df.drop(['isNormal'], axis=1)

    # 获取滞后一期的收益率
    df_pivot = df.pivot(index='Trdmnt', columns='Stkcd', values='Mretnd')
    df_pivot = df_pivot.shift(-1)
    df_pivot = df_pivot.unstack().reset_index().rename(columns={0: 'F1_Ret'})
    df = pd.merge(df, df_pivot, on=['Stkcd', 'Trdmnt'], how='left')
    df = stockFilter(df)
    df = df[df.Trdmnt >= '2015-01']

    return df


# 制作波动率因子
def get_vol_5():
    df = loadMainTrdData()
    df1 = df.set_index('Trdmnt').groupby('Stkcd')[['Mretnd']].rolling(5).std()
    return df1.dropna().reset_index().rename(columns={'Mretnd': 'vol_5'})


# 制作动量因子
def get_mom():
    df = loadMainTrdData()
    df1 = df.set_index('Trdmnt').groupby('Stkcd')[['Mretnd']].apply(lambda x: x / x.shift(5) - 1)
    return df1.dropna().reset_index().rename(columns={'Mretnd': 'mom'})


# 导入因子特征
def loadFactor():
    factor = pd.read_csv(Data_Dir + 'factor.csv')
    factor['Trdmnt'] = [x[:7] for x in factor.Trdmnt]

    return factor


# 导入行业数据
def loadCiticInd():
    df = pd.read_csv(Data_Dir + 'CiticIndustry.csv')
    df['Stkcd'] = [x[:6] for x in df['Stkcd']]
    df = df[['Stkcd', 'Stknme', 'Ind1']]
    df.rename(columns={'Ind1': 'Industry'}, inplace=True)

    return df


def loadAll():
    trd = loadMainTrdData()
    factor = loadFactor()
    indInfo = loadCiticInd()

    indInfo['Stkcd'] = [int(x) for x in indInfo.Stkcd]
    trd['Stkcd'] = [int(x) for x in trd.Stkcd]
    trd = pd.merge(trd, factor, on=['Trdmnt', 'Stkcd'], how='inner')
    trd = trd[trd.Trdmnt <= '2018-10']
    trd = pd.merge(trd, indInfo, how='left', on=['Stkcd'])

    return trd


trd = loadAll()

df = trd.copy()
df['Stkcd'] = [str(x).zfill(6) for x in df.Stkcd]
df = pd.merge(df, get_vol_5(), on=['Stkcd', 'Trdmnt'], how='left')
# df = pd.merge(df, get_mom(), on=['Stkcd', 'Trdmnt'], how='left')

var_list = ['vold', 'skewness', 'turnsd', 'egr', 'tang', 'sharechg', 'illq', 'lagretn',
            'aeavol', 'CFdebt', 'retmax', 'retvol', 'idvol', 'stdvold', 'LM']

# 缺失值处理
df.dropna(subset=var_list, inplace=True)
df = df[df.Industry.notnull()]
# print('缺失值情况\n', len(df) - df.count())


# 去掉上市不到半年的
df1 = df.copy()
df2 = df1.Trdmnt.groupby(df1.Stkcd).count()
df2 = df2.to_frame()
df2 = df2.rename(columns={'Trdmnt': 'shuliang'})
df2 = df2.reset_index()
df = pd.merge(df, df2, on=['Stkcd'], how='left')
df = df[df.shuliang >= 6]
del df['shuliang']


# MAD法
def extreme_feature_MAD(data, feature_name, num=3, p=1.4826):
    df = data.copy()
    median = df[feature_name].median()
    MAD = abs(df[feature_name] - median).median()
    df.loc[:, feature_name] = df.loc[:, feature_name].clip(lower=median - num * p * MAD, upper=median + num * p * MAD,
                                                           axis=1)

    return df


# 标准化处理
def get_zscore(data, feature_name):
    df = data.copy()
    df[feature_name] = (df[feature_name] - df[feature_name].mean()) / df[feature_name].std()

    return df


# 市值、行业中性化（回归法）
def data_scale_neutral_size_ind(data, CAP_name, industry_name, feature_name):
    df = data.copy()
    df_ind = pd.get_dummies(df[industry_name], columns=[industry_name])
    df_ind[CAP_name] = df[CAP_name]
    X = np.array(df_ind)

    for name in feature_name:
        y = np.array(df[name])
        reg = sm.OLS(y, X).fit()
        df[name] = reg.resid

    return df


# 3sigma法
def extreme_feature_3sigma(data, feature_name, num=3):
    df = data.copy()
    mean, std = df[feature_name].mean(), df[feature_name].std()
    df.loc[:, feature_name] = df.loc[:, feature_name].clip(lower=mean - num * std, upper=mean + num * std, axis=1)

    return df


# 异常值处理 - 3sigma方法
df = df.groupby(['Trdmnt']).apply(extreme_feature_3sigma, var_list)
df.index = range(len(df))

# 标准化 - Zscore
df = df.groupby(['Trdmnt']).apply(get_zscore, var_list)
df.index = range(len(df))

# 中性化 - 市值行业
df['Msmvttl'] = np.log(df['Msmvttl'])
df = df.groupby(['Trdmnt']).apply(data_scale_neutral_size_ind, 'Msmvttl', 'Industry', var_list)
df.index = range(len(df))

# 单分组
import scipy


def NWttest_1var(Y, L):
    Y = np.array(Y)
    mean = Y.mean()
    e = Y - mean
    T = len(Y)

    S = 0
    for l in range(1, L + 1):
        w_l = 1 - l / (L + 1)
        for t in range(l + 1, T + 1):
            S += w_l * e[t - 1] * e[t - 1 - l] * 2
    S = S + (e * e).sum()
    S = S / (T - 1)

    se = np.sqrt(S / T)
    tstat = mean / se
    pval = scipy.stats.t.sf(np.abs(tstat), T - 1) * 2

    return mean, se, tstat, pval


def cpt_vw_ret(group, avg_name, weight_name):
    d = group[avg_name]
    w = group[weight_name]

    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return np.nan


def get_stock_groups(data, sortname, groups_num):
    df = data.copy()
    labels = ['G0' + str(i) for i in range(1, groups_num + 1)]
    try:
        groups = pd.DataFrame(pd.qcut(df[sortname], groups_num, labels=labels).astype(str)).rename(
            columns={sortname: 'Group'})
    except:
        groups = pd.DataFrame(pd.qcut(df[sortname].rank(method='first'), groups_num, labels=labels).astype(str)).rename(
            columns={sortname: 'Group'})
    groups.index.name = 'ID'

    return groups


# Part 2 - Single Sort Analysis
def getSortRes(sortRes):
    sortRes = sortRes.reset_index().pivot(index='Trdmnt', columns='Group', values='Ret')
    sortRes = sortRes.shift(1).dropna()
    sortRes['HL'] = sortRes['G05'] - sortRes['G01']

    return sortRes


def get_single_sort(data, sortname, TimeName, groups_num, weighted):
    df = data.copy()
    df = df[df[sortname].notnull()]
    PortTag = df.groupby([TimeName]).apply(get_stock_groups, sortname, groups_num).reset_index().set_index('ID')
    df = pd.merge(df, PortTag['Group'], left_index=True, right_index=True)

    ret_name = 'F1_Ret'
    vwret = df.groupby([TimeName, 'Group']).apply(cpt_vw_ret, ret_name, weighted).to_frame().reset_index().rename(
        columns={0: 'Ret'})
    vwret = vwret.set_index(TimeName)
    ewret = df.groupby([TimeName, 'Group'])[ret_name].mean().to_frame().reset_index().rename(columns={ret_name: 'Ret'})
    ewret = ewret.set_index(TimeName)

    vwret = getSortRes(vwret)
    ewret = getSortRes(ewret)
    vwret_ttest = get_single_sort_nwtest(vwret)

    return vwret, ewret, vwret_ttest


def get_single_sort_nwtest(sortRes):
    res = {}
    L = int(4 * len(sortRes / 100) ** (2 / 9))
    for col in sortRes:
        Y = sortRes[col]
        mean, se, tstat, pval = NWttest_1var(Y, L)
        res[col] = {}
        res[col]['mean'] = mean
        res[col]['tstat'] = tstat
        res[col]['pval'] = pval
    res = pd.DataFrame(res)

    return res


TimeName = 'Trdmnt'
weighted = 'Msmvosd'
groups_num = 5

selected_factor = {}
for sortname in var_list:
    vwret, ewret, vwret_ttest = get_single_sort(df, sortname, TimeName, groups_num, weighted)
    selected_factor[sortname] = {}
    selected_factor[sortname]['mean'] = vwret_ttest['HL']['mean']
    selected_factor[sortname]['pval'] = vwret_ttest['HL']['pval']

selected_factor = pd.DataFrame(selected_factor).T
selected_factor = selected_factor.sort_values(['mean'])
selected_factor = selected_factor[selected_factor.pval < 0.05]


def get_panel_corr(df, TimeName, varList, method='pearson'):
    res = df.groupby([TimeName])[varList].corr(method=method)
    res = res.reset_index().rename(columns={'level_1': 'var'})
    corr = res.groupby(['var']).mean()

    return corr


relations = get_panel_corr(df, TimeName, list(selected_factor.index), method='pearson')
relations = relations[relations.index]

fontsize = 14
plt.figure(figsize=(30, 20))
plt.rc('font', weight='light', family='Times New Roman', style='normal', size=str(fontsize))
plt.tick_params(labelsize=fontsize)
sns.heatmap(relations, cmap='Blues', annot=True)
plt.show()


# Get Rank
def get_rank(df, TimeName, rank_list):
    rank_df = df.groupby([TimeName])[rank_list].rank()

    return rank_df


# Get Corr
def get_factor_corr(df, factorList, RetName, method='spearman'):
    corr_Res = df[factorList].corrwith(df[RetName], method=method)

    return corr_Res


# 等权重
def cal_factor_score_ew(df, TimeName, factorList):
    rank_res = get_rank(df, TimeName, factorList)
    score_ew = rank_res.mean(axis=1).to_frame().rename(columns={0: 'Score_EW'})

    return score_ew


# IC加权
def cal_factor_score_ic(df, TimeName, factorList, period):
    ic = df.groupby(TimeName).apply(get_factor_corr, factorList, 'F1_Ret')
    ic = ic.abs()
    rolling_ic = ic.rolling(period, min_periods=1).mean()
    weight = rolling_ic.div(rolling_ic.sum(axis=1), axis=0).reset_index()

    ranks = get_rank(df, TimeName, factorList)
    ranks['Trdmnt'] = df['Trdmnt']
    ranks['Tag'] = ranks.index
    weight = pd.merge(ranks[['Trdmnt', 'Tag']], weight, on=['Trdmnt'], how='left').set_index('Tag')
    weight.index.name = 'ID'
    weight.drop(['Trdmnt'], axis=1, inplace=True)
    ranks.drop(['Trdmnt', 'Tag'], axis=1, inplace=True)
    score_ic = ranks.mul(weight).sum(axis=1).to_frame().rename(columns={0: 'Score_IC'})

    return score_ic


# IR 加权
def cal_factor_score_ir(df, TimeName, factorList, period):
    ic = df.groupby(TimeName).apply(get_factor_corr, factorList, 'F1_Ret')
    ic = ic.abs()
    rolling_ic = ic.rolling(period, min_periods=1).mean()
    rolling_ic_std = ic.rolling(period, min_periods=1).std()
    ir = rolling_ic / rolling_ic_std
    ir.iloc[0, :] = rolling_ic.iloc[0, :]
    weight = ir.div(ir.sum(axis=1), axis=0).reset_index()

    ranks = get_rank(df, TimeName, factorList)
    ranks['Trdmnt'] = df['Trdmnt']
    ranks['Tag'] = ranks.index
    weight = pd.merge(ranks[['Trdmnt', 'Tag']], weight, on=['Trdmnt'], how='left').set_index('Tag')
    weight.index.name = 'ID'
    weight.drop(['Trdmnt'], axis=1, inplace=True)
    ranks.drop(['Trdmnt', 'Tag'], axis=1, inplace=True)
    score_ir = ranks.mul(weight).sum(axis=1).to_frame().rename(columns={0: 'Score_IR'})

    return score_ir


def get_all_Score(df, TimeName, factorList, period):
    score_ew = cal_factor_score_ew(df, TimeName, factorList)
    score_ic = cal_factor_score_ic(df, TimeName, factorList, period)
    score_ir = cal_factor_score_ir(df, TimeName, factorList, period)
    df['Score_EW'] = score_ew
    df['Score_IC'] = score_ic
    df['Score_IR'] = score_ir

    return df


df = get_all_Score(df, 'Trdmnt', list(selected_factor.index), 12)


def get_cum_ret(df, col):
    cum_ret = (df[col] + 1).prod() - 1

    return cum_ret


def get_annual_ret(df, col, m):
    annual_ret = (df[col] + 1).prod() ** (m / len(df)) - 1

    return annual_ret


def get_annual_vol(df, col, m):
    annual_vol = np.sqrt(m) * df[col].std()

    return annual_vol


def get_alpha_beta(df, port_col, bench_col, rf, m):
    beta = df[port_col].cov(df[bench_col]) / df[bench_col].var()
    alpha = (get_annual_ret(df, port_col, m) - rf) - beta * (get_annual_ret(df, bench_col, m) - rf)

    return alpha, beta


def get_sharpe_ratio(df, port_col, rf, m):
    sharpe = (get_annual_ret(df, port_col, m) - rf) / get_annual_vol(df, port_col, m)

    return sharpe


def get_info_ratio(data, port_col, bench_col, m):
    df = data.copy()
    df['diff'] = df[port_col] - df[bench_col]
    info = (get_annual_ret(df, port_col, m) - get_annual_ret(df, bench_col, m)) / (get_annual_vol(df, 'diff', m))

    return info


def maxDrawdownRate(X):
    endDate = np.argmax((np.maximum.accumulate(X) - X) / np.maximum.accumulate(X))
    if endDate == 0:
        return 0, len(X), endDate
    else:
        startDate = np.argmax(X[:endDate])

        return (X[startDate] - X[endDate]) / X[startDate], startDate, endDate


def get_max_drawdown(df, ret_col):
    X = np.array((1 + df[ret_col]).cumprod())
    maxDrawdown, i, j = maxDrawdownRate(X)

    return maxDrawdown, i, j


def rate_of_buying(pct_change):
    if pct_change > 1:
        rate = 0.6
    elif pct_change > 0.5:
        rate = 0.7
    elif pct_change > 0.15:
        rate = 0.8
    elif pct_change > 0.0:
        rate = 0.9
    elif pct_change > -0.1:
        rate = 1.1
    elif pct_change > -0.2:
        rate = 1.3
    elif pct_change > -0.3:
        rate = 1.5
    elif pct_change > -0.4:
        rate = 1.8
    else:
        rate = 2
    return (rate)


# 制作风控因子
def risk_managment():
    df = pd.read_csv(Data_Dir + 'hs300.csv')
    df['r'] = df['CLOSE'] / df['CLOSE'].rolling(60).mean() - 1
    df['ratio'] = df['r'].apply(rate_of_buying)
    df = df.rename(columns={'Unnamed: 0': 'Trdmnt'})
    df['month'] = df['Trdmnt'].apply(lambda x: x[:7])
    return df.groupby('month')['ratio'].mean()


def eval_strategy(data, bench_col, strategy_col, rf, m, isShow=False):
    r_bench = get_annual_ret(data, bench_col, m)
    r_strategy = get_annual_ret(data, strategy_col, m)
    r_cum_bench = get_cum_ret(data, bench_col)
    r_cum_strategy = get_cum_ret(data, strategy_col)
    vol_strategy = get_annual_vol(data, strategy_col, m)
    alpha, beta = get_alpha_beta(data, strategy_col, bench_col, rf, m)
    sharpe = get_sharpe_ratio(data, strategy_col, rf, m)
    info = get_info_ratio(data, strategy_col, bench_col, m)
    maxDrawdown1, i1, j1 = get_max_drawdown(data, strategy_col)
    maxDrawdown2, i2, j2 = get_max_drawdown(data, bench_col)

    # 策略评估
    if isShow:
        print(
            '回测期间: %s-%s' % (str(data.index[0].date()).replace('-', '/'), str(data.index[-1].date()).replace('-', '/')))
        print('总收益率: 策略: %.2f%%, 沪深300: %.2f%%' % (r_cum_strategy * 100, r_cum_bench * 100))
        print('年化收益率: 策略: %.2f%%, 沪深300: %.2f%%' % (r_strategy * 100, r_bench * 100))
        print('年化波动率: 策略: %.2f' % vol_strategy)
        print('最大回撤: 策略: %.2f%%, 沪深300: %.2f%%' % (-maxDrawdown1 * 100, -maxDrawdown2 * 100))
        print('策略最大回撤开始时间：%s, 最大回撤结束时间：%s' % (data.index[i1].date(), data.index[j1].date()))
        print('策略Alpha: %.2f%%, Beta: %.2f, 夏普比率: %.2f, 信息比率: %.2f' % (alpha * 100, beta, sharpe, info))

    perf_res = {'r_strategy': r_strategy, 'r_cum_strategy': r_cum_strategy, 'r_bench': r_bench,
                'vol_strategy': vol_strategy,
                'alpha': alpha, 'beta': beta, 'sharpe': sharpe, 'info': info, 'maxDrawdown': maxDrawdown1}

    return perf_res


def plotStrategyCurve(data, fig_dir):
    df = data.copy()
    fontsize = 24
    plt.close('all')
    plt.figure(figsize=(30, 15))
    plt.rc('font', weight='light', family='Times New Roman', style='normal', size=str(fontsize))
    plt.tick_params(labelsize=fontsize)
    df.index = pd.to_datetime(df.index)
    plt.plot(df.index, df['Strategy_NAV'], 'r-', df.index, df['Bench_NAV'], 'b--', linewidth=3)
    plt.xlabel('Date', fontsize=fontsize)
    plt.ylabel('Cumulative Net Value', fontsize=fontsize)
    plt.title('Strategy Peformance', fontsize=36)
    plt.legend(['Strategy', 'Benchmark'], fontsize=fontsize, loc=(.02, .90), frameon=False)
    plt.xlim(df.index[0], df.index[-1])
    sns.despine()
    plt.show()
    plt.savefig(fig_dir + 'MyStrategy' + '.jpg', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    perf_res = {}
    Fac_List = list(selected_factor.index)
    Fac_List.extend(['Score_EW', 'Score_IC', 'Score_IR'])

    rf = 0.0438
    bench = loadBenchMark()
    # print(bench)
    for sortname in Fac_List:
        vwret, ewret, vwret_test = get_single_sort(df, sortname, TimeName, groups_num, weighted)
        res = pd.merge(vwret, bench, how='left', left_index=True, right_index=True)
        if res['HL'].mean() < 0:
            res['Strategy_Ret'] = - res['HL']
        else:
            res['Strategy_Ret'] = res['HL']
        res['Strategy_NAV'] = (1 + res['Strategy_Ret']).cumprod()
        res['Bench_NAV'] = (1 + res['Bench_Ret']).cumprod()
        res.index = pd.to_datetime(res.index)

        perf_res[sortname] = eval_strategy(res, 'Bench_Ret', 'Strategy_Ret', rf, m=12)

    perf_res = pd.DataFrame(perf_res).T

    sortname = 'Score_IC'
    vwret, ewret, vwret_test = get_single_sort(df, sortname, TimeName, groups_num, weighted)
    res = pd.merge(vwret, bench, how='left', left_index=True, right_index=True)
    res = pd.concat([res,risk_managment()],axis=1).dropna()
    if res['HL'].mean() < 0:
        res['Strategy_Ret'] = - res['HL']
    else:
        res['Strategy_Ret'] = res['HL']
    res['Strategy_NAV'] = (1 + res['Strategy_Ret']*res['ratio']).cumprod()
    res['Bench_NAV'] = (1 + res['Bench_Ret']).cumprod()
    res.index = pd.to_datetime(res.index)
    temp = eval_strategy(res, 'Bench_Ret', 'Strategy_Ret', rf, m=12, isShow=True)
