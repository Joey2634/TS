import multiprocessing

def multiProcessings(num:int,paras:list,fun):
    """
    有返回值
    num:进程数
    paras：需要循环的数量
    fun：函数
    funparameter：fun函数需要的参数
    """
    result = []
    pool = multiprocessing.Pool(processes=num)
    for i in paras:
        if isinstance(i, dict):
            result.append(pool.apply_async(fun,  kwds=i))
        else:
            result.append(pool.apply_async(fun, args=tuple(i)))
    pool.close()
    pool.join()
    res = []
    for i in [i.get() for i in result if i.get()]:
        res.extend(i)
    return res