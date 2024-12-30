#-*- coding:utf-8 -*-

"""
Trading为统一交易接口。目前已经有如下实现类：
    A6.A6Trading
    CATS.CATSTrading
    rootNet.RootNetTrading
"""

class Trading(object):

    def __init__(self, env='test'):
        self.env = env

    def login(self, acctId=None, pwd=None, optId=None, optPwd=None):
        """

        :param acctId: ict
            资金账户信息。具体结构由各个Trading实现类定义。
        :param acctPwd:
            资金账户密码信息。具体结构由各个Trading实现类定义。
        :param optId:
            柜员号
        :param optPwd:
            柜员号密码
        :return:
        """
        """ 账户登录
        :param acctId: dict
            登录账户信息。具体结构由各个Trading实现类定义。
        :param pwd: dict
            登录密码信息。具体结构由各个Trading实现类定义。
        :return: None 自动显示登录账户的相关信息
        """
        pass

    def disconnect(self,close_time =None):
        """
        断开服务器连接并退出程序
        注意:使用跟网和恒生的twap策略下单时一定要设定合理的退出时间,否则会中断策略的执行.
        :param close_time:自定义退出时间,默认None,即立即断开服务器连接并退出
        :return:
        """
        pass

    def getStkInfo(self, windcode):
        """查询指定标的的实时行情
        :param: str
            万得代码 （例如： “600030.SH”）
        :return: 证券行情信息，各个Trading实现类自行封装。
        """
        pass

    def getAvaCash(self, where=None):
        """查询当前可用金额
        :param where: dict or None
            过滤条件字典. 字典格式为: {'acct': [<账户1>, <账户2>, ...]}. 其中账户对象与 login()中的账户描述一致。
            当where传入None或者没有'acct'字段时，则查询当前所有已登录账户。
        :return: dict
            符合查询条件的各账户可用金额。字典的key为账户str，value为金额。
        """
        pass


    def getCash(self, where=None):
        """查询当前总资金金额
        :param where: dict or None
            参见 getAvaCash()中()中的where参数说明
        :return: dict
            符合查询条件的各账户总资金金额。字典的key为账户str，value为金额。
        """
        pass

    def getOrders(self, where=None):
        """查询今日净委托。结果按照账户和标的物汇总。
        :param where: dict or None
            过滤条件字典，格式为:
                {'acct': [<账户1>, <账户2>, ...],
                 'windcode': [<万得代码1>, <万得代码2>, ...]}.
                其中账户对象与 login()中的账户描述一致。
                当字典中没有'acct'字段时，则对当前所有已登录账户查询。
                当字典中没有'windcode'字段时，则不限定查询标的。
            当Where为None时，则对所有已登录的账户查询。
        :return: pandas.DataFrame
            columns=[
                <多级账户字段>,   # 各Trading实现类自行定义
                "WIND_CODE",    #万得代码
                "SECURITY_CODE",  # 证券代码
                "MARKET_TYPE",  # 市场类型，如"SH","SZ"
                "TRADE_TYPE",   # 交易类型，"B","S"
                "ORDER_VOLUME"  # 委托量(单位:股)
                ]
        """
        pass

    def getPositions(self, where=None):
        """查询当前持仓。
        :param where: dict or None
            参见 getOrders()中的where参数说明
        :return: pandas.DataFrame
            columns=[
                <多级账户字段>,   # 各Trading实现类自行定义
                "WIND_CODE",    # 万得代码
                "MARKET_TYPE", # 市场类型，如"SH","SZ"
                "SECURITY_CODE", # 证券代码
                "SECURITY_NAME", # 证券名称
                "POSITION", # 当前持仓量
                "NOTIONAL", # 市值
                "COST"      # 持仓成本(单价)
                ]
        """
        pass

    def getTrades(self, where=None):
        """查询当日成交。结果按照账户和标的物汇总。
        :param where: dict or None
            参见 getOrders()的where参数
        :return: pandas.DataFrame
            columns=[
                <多级账户字段>,   # 各Trading实现类自行定义
                "WIND_CODE",    #万得代码
                "SECURITY_CODE", # 证券代码
                "MARKET_TYPE",  # 市场类型，如"SH","SZ"
                "SECURITY_NAME",# 证券名称
                "TRADE_TYPE",   # 交易类型，"B","S"
                "TRADE_PRICE",  # 当日成交成本(单价)
                "TRADE_VOLUME", # 成交总数量(股)
                "TRADE_AMOUNT"  # 成交总金额
            ]
        """
        pass

    def sendOrder(self, orders, algo, syncFlag=False):
        """下委托
        :param orders: dict
            委托单字典。字典定义为：
              {
               <账户1>: [<order>,<order>,...],
               <账户2>: [<order>,<order>,...],
                ...
              }
            其中:
              账户对象与 login()中的账户描述一致;
              order为 class Order 的实例
        :param algo:
            算法交易实例。具体参见各个实现类的说明。
        :param syncFlag: bool
            同步标志
        :return: None
        """
        pass

    def getOriginalOrder(self, where=None):
        """查询可撤销的原始委托单
        :param where: dict or None
            参见 getOrders()的where参数
        :return: pandas.DataFrame
            columns=[
                <多级账户字段>, # 各Trading实现类自行定义
                "SECURITY_CODE", # 证券代码
                "WIND_CODE",     #万得代码
                "MARKET_TYPE",   # 市场类型，如"SH","SZ"
                "TRADE_TYPE",    # 交易类型，"B","S"
                "ORDER_VOLUME",  # 委托量
                "FILLED_VOLUME", # 实际成交量
                "ORDER_PRICE",   # 委托价格
                "CANCELABLE",    # 是否可取消，"Y","N"
                "CANCEL_KEY"     # cancel key，用于 cancelOrder()接口撤销委托
                ]
            其中"CANCEL_KEY"列可以取出，转换为list后，作为cancelOrder的入参。
            example:
                #assert isinstance(trading, Trading)
                orders = trading.getOriginalOrder()
                trading.cancelOrder(orders["CANCEL_KEY"].tolist())
        :seealso: cancelOrder()
        """
        pass

    def cancelOrder(self, cancel_keys):
        """撤销委托
        :param cancel_keys: list or set of str
            需要撤销的keys. 一般可以从getOriginalOrder()中的"CANCEL_KEY"列获取
        :return: None
        :seealso: getOriginalOrder()
        """
        pass
