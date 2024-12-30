from backtest.BackTest import BackTest

if __name__ == '__main__':
    backtest = BackTest(['S-L-16|LastPrice|CLOSE|RISK-47'], '20150101', '20210115')
    backtest.run()
    backtest.saveResult2DB()