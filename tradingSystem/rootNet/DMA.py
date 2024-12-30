#-*- coding:utf-8 -*-
import re
import logging
Logger = logging.getLogger()
from CTSlib.AlgoAPI import ApiException,printObject




class DMA():

    def execute(self,tradeServer, orderInfo, syncFlag=True):
        """
        :param tradeServer: server类
        :param orderInfo: 订单信息
        :param syncFlag: 同步异步标志,True 为同步
        :return:
        """
        # 异步请求方法返回包头
        if syncFlag == True:
            try:
                newOrderResponse = tradeServer.orderNew (orderInfo, syncFlag)
                Logger.info("{}委托成功 返回信息:".format(orderInfo.stkId) + self._getObjectInfo(newOrderResponse))
                print("{}委托成功!".format(orderInfo.stkId))
                # print("""万得代码为{}的订单下单成功,返回信息如下:
                # 委托金额:{}
                # 合同号:{}
                # 可用金额:{}""".format(orderInfo.stkId,newOrderResponse.orderAmt,newOrderResponse.contractNum,newOrderResponse.usableAmt))
            except ApiException as API_E:
                Logger.error(API_E)
                print("万得代码为{}的订单下单失败,订单信息及错误信息如下:\n{}".format(orderInfo.stkId,API_E))
                printObject(orderInfo)
        else:
            tradeServer.orderNew (orderInfo, syncFlag)


    def _getObjectInfo(self, obj):
        attrs = dir(obj)
        result = ""
        p = re.compile("__.*__")
        for attr in attrs:
            m = p.search(attr)
            if m == None:
                result += "." + str(attr) + "=" + str(getattr(obj, attr)) + "\n"
        return result