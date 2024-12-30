# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time : 2020/12/25 下午5:31
# @Author : lxf
# @File : logger.py
# @Project : ai-investment-manager

import os
import arrow
import logging
from logging.handlers import RotatingFileHandler

def get_level(level):
    if isinstance(level, str)is False:
        return level

    level = level.lower()

    if level == "warn" or level == "warning":
        return logging.WARN
    elif level == "error":
        return logging.ERROR
    elif level == "info":
        return logging.INFO
    elif level == "debug":
        return logging.DEBUG
    else:
        return logging.DEBUG

def setup_logging_by_params(filename = '',level = '',maxBytes=500 * 1024 * 1024):
    date = str(arrow.now().date())
    if not os.path.exists(os.getcwd()+'/logs'):
        os.mkdir(os.getcwd()+'/logs')
    filename = 'logs/'+date + filename + '.log'
    format = '%(asctime)s %(process)s-%(levelname)s %(message)s[%(filename)s:%(lineno)d]'
    datefmt = '%Y-%m-%d%H:%M:%S'
    Rthandler = RotatingFileHandler(filename=filename, maxBytes= maxBytes, backupCount=10)
    Rthandler.setLevel(get_level(level))
    formatter = logging.Formatter(fmt=format,datefmt=datefmt)
    Rthandler.setFormatter(formatter)
    logging.getLogger('').addHandler(Rthandler)
    logging.getLogger().setLevel(get_level(level))


if __name__ == '__main__':
    setup_logging_by_params(filename='test',level='debug')
    loger = logging.getLogger('test')
    loger.debug('debug')