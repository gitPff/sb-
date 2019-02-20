#!/usr/bin/env python
# coding=utf-8
import json
import redis
import parser_except


def gen_redis_key(parser):
    key = '%s_%s_%s_%s' % (parser.source_type, parser.task.tid, parser.task.content, parser.task.order_no)
    return key


def save_spider_status(parser, session, customized=None, ex=60 * 10):
    """
    :param parser:
    :param session:
    :param customized:  存储每个parser的特殊参数 e.g token
    :param ex: redis的超时时间
    :return:
    """
    r = redis.Redis(host='10.10.118.248', port=6379, password='MiojiRedis123')
    key = gen_redis_key(parser)
    r.setex(key, json.dumps({'session': session, 'customized': customized}), ex)


def load_spider_status(parser):
    r = redis.Redis(host='10.10.118.248', port=6379, password='MiojiRedis123')
    key = gen_redis_key(parser)
    spider_status = r.get(key)
    if spider_status is None:
        raise parser_except.ParserException(13, '未找到spider_status')
    else:
        return json.loads(spider_status)
