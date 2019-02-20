#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @Time    : 2018/4/24 下午4:58
# @Author  : Fan bowen
# @Site    : 
# @File    : spider_queue_qps.py
# @Software: PyCharm

from threading import Thread
import requests
import random
import time
from utils import current_log_tag
from logger import logger


class TimeoutException(Exception):
    pass


ThreadStop = Thread._Thread__stop  # 获取私有函数


# 此装饰器功能为让一个函数控制在一定时间内， 如果超时 抛出错误
def time_limited(timeout):
    def decorator(function):
        def decorator2(*args, **kwargs):
            class TimeLimited(Thread):
                def __init__(self, _error=None, ):
                    Thread.__init__(self)
                    self._error = _error

                def run(self):
                    try:
                        self.result = function(*args, **kwargs)
                    except Exception, e:
                        self._error = e

                def _stop(self):
                    if self.isAlive():
                        ThreadStop(self)

            t = TimeLimited()
            t.start()
            t.join(timeout)

            if isinstance(t._error, TimeoutException):
                t._stop()
                raise TimeoutException('timeout for %s' % (repr(function)))

            if t.isAlive():
                t._stop()
                raise TimeoutException('timeout for %s' % (repr(function)))

            if t._error is None:
                return t.result

        return decorator2

    return decorator


static = {}


# @time_limited(300)
def queue_and_qps(post):
    post['is_api'] = True
    if not post:
        return False
    try:
        qid = str(time.time()) + str(random.choice(list(range(1000))))
        post['qid'] = qid
        res = int(requests.post('http://10.19.23.81:8001/main', json=post, timeout=100).content)
        now = int(time.time())
        if res != now:
            # print '存取不同步{0}|{1}'.format(res, now)
            return False
        else:
            return True
    except TimeoutException as why:
        # 此处是超时错误， 记录日志即可
        return None
    except Exception as why:
        # print str(why) + "报警"
        return None

if __name__ == '__main__':
    import redis

    r = redis.from_url("redis://:MiojiRedis99@10.19.198.92:6379/1")

    import datetime
    import gevent
    import gevent.monkey

    gevent.monkey.patch_all()
    time_record_point1 = datetime.datetime.now()
    spawn_list = []
    for i in range(100):
        spawn_list.append(gevent.spawn(queue_and_qps, r, {
            "source_name": "tuniu_search"
        }))
    gevent.joinall(spawn_list)
    # print [i.get() for i in spawn_list]
    time_record_point2 = datetime.datetime.now()
    print '总耗时  {0}'.format((time_record_point2 - time_record_point1).seconds)
