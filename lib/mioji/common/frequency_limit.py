#!/usr/bin/python
# -*- coding: UTF-8 -*-

from redlock import Redlock
import time
import uuid
import redis
from logger import logger


# 之前的router心跳redis
#   心跳：db=1
#   请求频率控制：db=2
redis_config = {"host": "10.10.173.116", "port": 6379, "password": "MiojiRedisOrzSpiderVerify", "db": 2}

# 频率限制配置: time(s) 时间内 count 次请求限制。
#   mode：hard-严格模式，如20s 2个那么每两个请求间隔 10s；
#   soft-最近20s内不没达到2个请求就可以解析进行
#   task_enable 是否任务级控制，如果一个任务就一个请求不需要(设置false)减小消耗
limit_config = {"rail_search": {"count":5,"time":3,"mode":"hard","task_enable":True},
                "daolv_search": {"count":20,"time":2,"mode":"hard","task_enable":False},
                "dotw_search": {"count":20,"time":2,"mode":"hard","task_enable":False},
                "yinling_all": {"count":2,"time":2,"mode":"hard","task_enable":False},
                "igola_search": {"count":10,"time":2,"mode":"hard","task_enable":True},
                "meiya_search": {"count":9,"time":60,"mode":"hard","task_enable":False},
                "zhenlv_search": {"count":2,"time":2,"mode":"hard","task_enable":False},
                "tongcheng_search": {"count":100,"time":2,"mode":"hard","task_enable":False},
                "tuniu_search": {"count":1,"time":1,"mode":"hard","task_enable":True},
                "gta_search": {"count":12,"time":2,"mode":"hard","task_enable":False},
                "bedsonline_search": {"count":4,"time":2,"mode":"hard","task_enable":False},
                "miki_search": {"count":25,"time":2,"mode":"hard","task_enable":False},
                "veturis_search": {"count":3,"time":2,"mode":"hard","task_enable":False},
                "aic_search": {"count":10,"time":2,"mode":"hard","task_enable":False},
                "ean_search": {"count":40,"time":2,"mode":"hard","task_enable":False},
                "zuzuche_search": {"count":5,"time":1,"mode":"hard","task_enable":False},
                "hanglu_search": {"count":1,"time":2,"mode":"hard","task_enable":False},
                "huizuche_search": {"count":4,"time":1,"mode":"hard","task_enable":False}}


class QuencyLimit:
    """
    redis_config redis配置
        LIKE: {"host": "localhost"}

    频率限制配置: time(s) 时间内 count 次请求限制。
        mode：hard-严格模式，如20s 2个那么每两个请求间隔 10s；
        soft-最近20s内不没达到2个请求就可以解析进行

        LIKE:
        {"baidu": {"count": 2, "time": 20, "mode": "soft"},
        "google": {"count": 2, "time": 20, "mode": "hard"}}
    """
    def __init__(self, redis_config, quency_config):
        self.quency_config = quency_config
        self.redlock = Redlock([redis_config])
        self.rds = redis.Redis(**redis_config)

    def dblock_wait(self, key, task, timeout):
        self.quency_config = limit_config[key]
        return ReqLimitLock(key, task, timeout, self.quency_config, self.redlock, self.rds)


first_cache = {}


class ReqLimitLock(object):

    WAITE_TIME = 0.05
    # 请求中
    REQ_ING_CACHE_TIME = 2
    # 等待中缓存, 如果没开始更新缓存
    TASK_WAITE_CACHE_TIME = 3
    # 任务缓存保留30s
    TASK_IN_CACHE_TIME = 30
    # 请求中保留 30s
    REQ_CACHE_TIME = 30

    def __init__(self, key, task, timeout, quency_config, redlock, rds):
        self.key = key
        self.task = task
        # 当前队列配置
        self.config = quency_config
        self.max_count = self.config['count']
        self.task_enable = self.config['task_enable']

        self.redlock = redlock
        self.rds = rds
        self.req_id = str(uuid.uuid1())
        self.task_id = task['task_id']

        # 等待中任务key
        self.task_wait_queue_group = '{0}-wait*'.format(self.key)
        self.task_wait_queue_key = '{0}-wait-{1}-{2}'.format(self.key, self.task_id, self.req_id)

        timeout_max = (timeout * self.max_count / self.config['time'])
        # print 'timeout_max', timeout_max
        if self.__current_wait_count() > timeout_max:
            raise Exception('队列满了')

        # task first in cache
        self.task_first_group = '{0}-task-first-in-*'.format(self.key, self.task_id)
        self.task_first_in_key = '{0}-task-first-in-{1}'.format(self.key, self.task_id)
        self.task_intime = self.__task_first_intime()
        self.rds.setex(self.task_first_in_key, self.task_intime, ReqLimitLock.TASK_IN_CACHE_TIME)

        # task wait record
        self.rds.setex(self.task_wait_queue_key, self.task_intime, ReqLimitLock.TASK_WAITE_CACHE_TIME)

        # 请求中
        self.req_key_group = '{0}-reqing-{1}*'.format(self.key, self.task_id)
        self.req_key = '{0}-reqing-{1}-{2}'.format(self.key, self.task_id, self.req_id)

        if self.config['mode'] == 'hard':
            self.is_hard_mode = True
            self.limit_key = '{0}-hard'.format(key)
            self.min_dur = self.config['time'] * 1000000 / self.config['count']
        else:
            self.is_hard_mode = False
            self.limit_key = '{0}-soft:{1}'.format(self.key, self.req_id)

    def __task_first_intime(self):
        intime = self.rds.get(self.task_first_in_key)
        if intime:
            return intime
        else:
            return str(self.redis_time())

    def __current_wait_count(self):
        keys = self.rds.keys(self.task_wait_queue_group)
        # print keys
        c = len(keys)
        # print 'current', c
        return c

    def __current_req_count(self):
        # 理论上keys最大数是配置的count 不会太多，所以直接用keys
        return len(self.rds.keys(self.req_key_group))

    def __is_first(self):
        # 不控制
        if not self.task_enable:
            return True
        s = time.time() * 1000
        is_first = True
        if self.__current_wait_count() > 1:
            keys = self.rds.keys(self.task_wait_queue_group)
            # print keys
            for k in keys:
                if k == self.task_wait_queue_key:
                    continue
                it = first_cache.get(k, None)
                if not it:
                    it = self.rds.get(k)
                    first_cache[it] = first_cache
                # print it
                if it:
                    if self.task_intime > self.rds.get(k):
                        is_first = False
                        break
        print time.time() * 1000 - s
        return is_first

    def redis_time(self):
        """
        redis time
        :return:
        """
        rt = self.rds.time()
        nt = rt[0] * 1000000 + rt[1]
        return nt

    def __check_cango(self):
        if self.is_hard_mode:
            # 上次请求发出时间
            last = self.rds.get(self.limit_key)
            # redis当前时间ms
            nt = self.redis_time()
            if last:
                dur = nt - long(last)
                # print "dur, last", dur, last
                if dur >= self.min_dur:
                    return True
            else:
                return True
        else:
            keys = self.rds.keys('{0}-soft:*'.format(self.key))
            if len(keys) < self.max_count:
                return True
        return False

    def __go(self):
        # print self.req_key, 'GOOO'
        print self.redis_time()
        if self.is_hard_mode:
            # 记录当次请求执行时间
            self.rds.set(self.limit_key, self.redis_time())
        else:
            # 记录当次请求执行
            self.rds.setex(self.limit_key, '', self.config['time'])

        # 删除等待中任务记录
        self.rds.delete(self.task_wait_queue_key)
        # 记录请求中的任务
        self.rds.setex(self.req_key, self.task_intime, ReqLimitLock.REQ_CACHE_TIME)

    def __enter__(self):
        """
        :param key:
        :param timeout: TODO
        :return: True 正常控制；False 其他
        """
        while True:
            with red_lock(self.redlock, self.key):
                if self.__check_cango():
                    if self.__is_first():
                        self.__go()
                        break
            # 更新等待
                self.rds.setex(self.task_wait_queue_key, self.task_intime, ReqLimitLock.TASK_WAITE_CACHE_TIME)
            time.sleep(ReqLimitLock.WAITE_TIME)
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 删除请求中任务
        try:
            self.rds.delete(self.req_key)

            # 如果等待队列中无等待任务，删除task 进入时间记录
            if self.__current_wait_count() == 0:
                if first_cache.has_key(self.task_wait_queue_key):
                    del first_cache[self.task_wait_queue_key]
                self.rds.delete(self.task_first_in_key)
        except Exception as e:
            logger.debug('新qps问题' + str(e))


class SlaveLock:

    def __init__(self, redlock, key):
        self.key = key
        self.redlock = redlock
        self.lock = None

    def __enter__(self):
        while True:
            lock = self.redlock.lock(self.key, 1000)
            if not lock:
                time.sleep(0.12)
            else:
                self.lock = lock
                return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redlock.unlock(self.lock)


def red_lock(redlock, key):
    return SlaveLock(redlock, key)


def init_default_limiter():
    # frequency_limit.init(limit_config, redis_config)
    req_limit = QuencyLimit(redis_config, limit_config)
    return req_limit


default_limiter = init_default_limiter()

if __name__ == '__main__':
    default_limiter.rds.setex('testxx', '11', 5)
    default_limiter.rds.setex('testxx1', '11', 5)
    default_limiter.rds.setex('testxx2', '11', 5)

    # keys = default_limiter.rds.keys('test*')
    # for k in keys:
    #     print default_limiter.rds.get(k)
    # for i in default_limiter.rds.scan(match='test*'):
    #     print i
    # print default_limiter.rds.time()
    a = {'a': 1}
    del a['a']
    print a


