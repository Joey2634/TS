#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@author:ai
@file:Account.py
@time:2020/05/20
"""
import socket
import uuid

from tradingSystem.CATS.catsserverapi.catsConfig import hdSerial


class Account():

    def __init__(self,CATS_ACCT = "701896",CATS_PWD = "111111",
                     TRADE_ACCT = "010000510063",TRADE_ACCTTYPE = "G30",
                 TRADE_PWD = "111111"):
        """
        :param CATS_ACCT:  cats账户
        :param CATS_PWD:   cats账户密码
        :param TRADE_ACCT: 资金账户
        :param TRADE_ACCTTYPE: 资金账户类型
        :param TRADE_PWD:  资金账户密码
        """
        self.catsAcct = CATS_ACCT
        self.catsAcctPwd = CATS_PWD
        self.tradeAcct = TRADE_ACCT
        self.tradeAcctType = TRADE_ACCTTYPE
        self.tradeAcctPwd = TRADE_PWD

    def __str__(self):
        return "catsAcct:{},catsAcctPwd:{},tradeAcct:{},tradeAcctType:{},tradeAcctPwd:{}".format(
            self.catsAcct,
            self.catsAcctPwd,
            self.tradeAcct,
            self.tradeAcctType,
            self.tradeAcctPwd
        )


class LocalOsInfo():
    def __init__(self):
        """
        :param LOCAL_IP: 本机ip
        :param macAddr:  本机 物理地址
        :param hdSerial: 硬盘序列号
        """
        self.localIp = self.getIp()
        self.macAddr = self.getMAC()
        self.hdSerial = self.getHDSerial()
        pass

    def getIp(self):
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        addr, port = csock.getsockname()
        print("IP  {}".format(addr))
        return addr

    def getMAC(self):
        mac = uuid.uuid1().hex[-12:]
        macAddr = ":".join([mac[i:i+2] for i in range(0,len(mac)-1,2)])
        print('MAC  {}'.format(macAddr))
        return macAddr

    def getHDSerial(self):
        # p = Popen(['lshw'],stdout=PIPE)
        # data = p.stdout.read()
        # print(data)
        return hdSerial







if __name__ == '__main__':
    li = LocalOsInfo()
    li.getHDSerial()






