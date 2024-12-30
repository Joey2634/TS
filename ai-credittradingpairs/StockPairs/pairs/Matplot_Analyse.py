




# 展示策略收益曲線
def show_returns():
    pass

def Stop_loss():
    pass


def cal_returns(df):
    df1 = df.cumsum()
    df1 = df1.iloc[2:]
    df_ret = df1.pct_change()
    df1.to_csv('daily_money.csv')
    df_ret.cumsum().plot(figsize=(14, 8), grid=True)
    plt.show()
    return df1

