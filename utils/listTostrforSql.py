# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2021/1/20 上午10:32
# @Author : lxf
# @File : listTostrforSql.py
# @Project : ai-investment-manager


def tostr(value:list):
    return str(value).replace("[", "").replace("]", "")