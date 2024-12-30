#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:Order.py
@time:2020/06/02
"""


class Order():

    def __init__(self, wind_code: str = "", trade_side: str = "", orderType: str = "0", \
                 price_value: str = "", qty: int = 0, order_param: str = ""):
        """

        :param wind_code: 标的代码
        :param trade_side: 交易方向
                            普通:
                             1	买入 或 担保品买入
                             2	卖出 或 担保品卖出
                            ETF
                             F	ETF申购
                             G	ETF赎回
                            融资融券:
                             A	融资买入
                             B	融券卖出
                             C	买券还券
                             D	卖券还款
                             E	先买券还券，后担保品买入
                            期货/期权:
                             FA  开多仓（开仓买入）
                             FB  开空仓（开仓卖出）
                             FC  平空仓（平仓买入）
                             FD  平多仓（平仓卖出）

        :param orderType:  类型:
                            上海: 0 限价单
                            深圳: 0 限价单

        :param price_value: 委托价格
        :param qty: 委托数量
        :param order_param:
        """

        self.symbol = wind_code


