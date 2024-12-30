#-*- coding:utf-8 -*-

def enum(**enums):
    return type('Enum', (), enums)

TradeType = enum(
    LIMIT = "0", # 限价单
    Q = "Q", # 市价单（对手方最优价格）(SZ)
    R = "R", # 市价单（最优五档即时成交剩余转限价）(SH)
    S = "S", # 市价单（本方最优价格）(SZ)
    T = "T", # 市价单（即时成交剩余撤销）(SZ)
    U = "U", # 市价单（最优五档即时成交剩余撤销）(SH,SZ)
    V = "V" # 市价单（全额成交或撤单）(SZ)
)

class Order(object):
    def __init__(self, windCode, orderType, orderQty=0, orderPrice=0, tradeType=TradeType.LIMIT, acct=None):
        """ 生成订单(母单)
        :param windCode: str
            万得代码
        :param orderType: str of 'B' or 'S'
            买卖方向， 'B'=买, 'S'=卖
        :param orderQty: int
            目标量
        :param orderPrice: float
            限价
        :param tradeType: enum TradeType or str
            TradeType.LIMIT or "0": # 限价单，默认值
            TradeType.Q or "Q",     # 市价单（对手方最优价格）(SZ)
            TradeType.R or "R",     # 市价单（最优五档即时成交剩余转限价）(SH)
            TradeType.S or "S",     # 市价单（本方最优价格）(SZ)
            TradeType.T or "T",     # 市价单（即时成交剩余撤销）(SZ)
            TradeType.U or "U",     # 市价单（最优五档即时成交剩余撤销）(SH,SZ)
            TradeType.V or "V"      # 市价单（全额成交或撤单）(SZ)
            注: 目前根网和A6只支持限价单，CATS同时支持限价单和市价单
        """
        self.windCode = windCode
        self.orderType = orderType
        self.orderQty = orderQty
        self.orderPrice = orderPrice
        self.tradeType = tradeType
        self.acctId = acct


    def __repr__(self):
        return str(self.windCode)+","+str(self.orderType)+","+str(self.orderQty)+","+str(self.orderPrice)


class NotionalOrder(object):
    def __init__(self, windCode, orderType, orderNotional, orderPrice=None, tradeType=TradeType.LIMIT, acct=None):
        """ 生成订单(母单)
        :param windCode: str
            万得代码
        :param orderType: str of 'B' or 'S'
            买卖方向， 'B'=买, 'S'=卖
        :param orderNotional: int
            目标总价格
        :param orderPrice: float
            限价
        :param tradeType: enum TradeType or str
            TradeType.LIMIT or "0": # 限价单，默认值
            TradeType.Q or "Q",     # 市价单（对手方最优价格）(SZ)
            TradeType.R or "R",     # 市价单（最优五档即时成交剩余转限价）(SH)
            TradeType.S or "S",     # 市价单（本方最优价格）(SZ)
            TradeType.T or "T",     # 市价单（即时成交剩余撤销）(SZ)
            TradeType.U or "U",     # 市价单（最优五档即时成交剩余撤销）(SH,SZ)
            TradeType.V or "V"      # 市价单（全额成交或撤单）(SZ)
            注: 目前根网和A6只支持限价单，CATS同时支持限价单和市价单
        """
        self.windCode = windCode
        self.orderType = orderType
        self.orderNotional = orderNotional
        self.orderPrice = orderPrice
        self.tradeType = tradeType
        self.acctId = acct
