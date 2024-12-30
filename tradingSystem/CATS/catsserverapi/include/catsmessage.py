#!/usr/bin/env python3
#-*- coding:utf-8 -*-
"""
@author:ai
@file:catsmessage.py
@time:2020/05/18
"""

import ctypes

# 客户端信息
class ClientLocationInfo(ctypes.Structure):
	_fields_ = [
		('ip',ctypes.c_char * 33),      # IP地址
		('macAddr',ctypes.c_char * 33), # MAC地址
		('hdSerial',ctypes.c_char * 33) # 硬盘序列号
	]



# Cats账户信息（登陆后）.
# 除了catsAcctLogin请求外，其余请求都含有该结构体。这些请求均需要设置正确的cats用户名和token串用于身份校验。
#

class CatsAccountData(ctypes.Structure):
	_fields_ = [
		('catsAcct',ctypes.c_char_p),  # cats账户名
		('catsToken',ctypes.c_char_p)  # cats账户登陆成功后得到的token串
	]




# struct CATSSvcResponseBase {
# 	virtual ~CATSSvcResponseBase() { };
# 	STDSTR errCode;
# 	STDSTR errMsg;
# 	virtual STDSTR toString() { return "errCode=" + errCode + ",errMsg=" + errMsg;  };
# };


# 登录回调函数的传参
class CATSLoginSvcResponse(ctypes.Structure):
	_fields_ = [
		('catsAcct',ctypes.c_char_p),
		('catsToken',ctypes.c_char_p)
	]