#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月6日

@author: dujun
'''
from datetime import datetime
import functools
from logger import logger
from collections import defaultdict
# import mioji.common.pool
from utils import current_log_tag

func_count_dict = defaultdict(int)


def func_time_logger(fun):
    if fun.__dict__.get('mioji.aop_utils.logger', False):
        return fun
    fun.__dict__['mioji.aop_utils.logger'] = True

    @functools.wraps(fun)
    def logging(*args, **kw):
        func_count_dict[fun.__name__] += 1
        begin = datetime.now()
        logger.debug(current_log_tag() + '函数 {0} call start'.format(fun.__name__))
        result = fun(*args, **kw)
        end = datetime.now()
        logger.debug(current_log_tag() + '函数 {0} call end'.format(fun.__name__))
        # logger.debug(current_log_tag() + ',函数,%s,耗时,%s,当前运行,%s,个此函数,当前,%s,协程', fun.__name__, (end - begin),
        #              func_count_dict[fun.__name__], mioji.common.pool.pool.size)
        func_count_dict[fun.__name__] -= 1
        return result

    return logging


def cost_time(func):
    """
    该方法用于统计写redis/MQ耗时
    :return: result函数运行结果 cost:函数耗时
    """

    @functools.wraps(func)
    def wapper(*args, **kwargs):
        operation_info = {}
        begin = datetime.now()
        func_result = func(*args, **kwargs)
        end = datetime.now()
        func_cost_time = round((end - begin).total_seconds(), 3)
        operation_info.update({'result': func_result, 'cost_time': func_cost_time})
        return operation_info

    return wapper
