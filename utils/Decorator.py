from operator import methodcaller
import time
from functools import wraps


# 装饰类方法的装饰器,并可以通过传递类方法.功能:在被修饰的方法之调用新增方法!
def doAfter(funName):
    def wrapper(fun):
        def inner(*args, **kwargs):
            cls = args[0]
            windcode = args[1]
            result = fun(*args, **kwargs)
            methodcaller(funName, windcode, result)(cls)
            return result

        return inner

    return wrapper


def func_timer(function):
    """
    用装饰器实现函数计时
    :param function: 需要计时的函数
    :return: None
    """

    @wraps(function)
    def function_timer(*args, **kwargs):
        print('[Function: {name} start...]'.format(name=function.__name__))
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print('[Function: {name} finished, spent time: {time:.2f}s]'.format(name=function.__name__, time=t1 - t0))
        return result

    return function_timer
