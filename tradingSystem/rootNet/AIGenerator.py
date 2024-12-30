# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 20:14:08 2018

@author:
"""

# 从全局变量 获取变量信息
import threading
from collections import defaultdict

from apscheduler.schedulers.background import BackgroundScheduler

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import contextlib
from multiprocessing import Lock as PLock


class B():
    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        for name, item in globals().items():
            if item == self and name != '':
                self.name = name
                print(name)
                return name


def singleGen(cls, *args, **kw):
    instance = {}

    def _singleGen():
        if cls not in instance:
            instance[cls] = cls(*args, **kw)
        return instance[cls]

    return _singleGen


@singleGen
class AIGenerator(object):
    def __init__(self):
        self.id = ("%08d" % x for x in range(1, 99999))


@singleGen
class SchedulerNum(object):
    def __init__(self):
        self.num = (x for x in range(1, 99999999))


executors = {
    'default': ThreadPoolExecutor(1000),
    'processpool': ProcessPoolExecutor(30),
    # 'default':ProcessPoolExecutor(30)
}
executors_01 = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(30),
    # 'default':ProcessPoolExecutor(30)
}


@singleGen
class Scheduler(object):
    def __init__(self):
        print("实例化定时器!")
        self.Scheduler = BackgroundScheduler(executors=executors)


@singleGen
class Scheduler_trading(object):
    def __init__(self):
        print("实例化定时器!")
        self.Scheduler = BackgroundScheduler(executors=executors_01)


@singleGen
class SingleLock(object):
    def __init__(self):
        self.singleLock = threading.RLock()


@singleGen
class SingleLockOfA6(object):
    def __init__(self):
        self.singleLock = threading.Lock()


@singleGen
class OrderCache(object):
    def __init__(self):
        print('实例化全局唯一锁')
        self.singleLockOfOrder = threading.Lock()
        self.order_cache = defaultdict(lambda: 0)


@singleGen
class TimeOutLockFactor(object):
    def __init__(self):
        self.singleLock = PLock()


@contextlib.contextmanager
def SingleTimeOutLock(timeout=-1):
    """
    #单例超时锁
    :param timeout:超时时间设定
    :return:
    """
    Lock = TimeOutLockFactor().singleLock
    try:
        Lock.acquire(timeout=timeout)
        yield Lock
    except:
        pass
    finally:
        Lock.release()


@contextlib.contextmanager
def TimeOutLock(outlock, timeout=-1):
    """
    普通超时锁
    :param outlock:外部传入普通锁
    :param timeout:超时时间
    :return:
    """
    Lock = outlock
    try:
        Lock.acquire(timeout=timeout)
        yield Lock
    except:
        pass
    finally:
        Lock.release()


if __name__ == "__main__":
    a = AIGenerator()
    print(next(a.id))
    c=AIGenerator()
    print(next(c.id))
    print(next(c.id))
    print(next(a.id))
    print(next(c.id))

