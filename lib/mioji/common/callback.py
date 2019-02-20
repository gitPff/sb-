# -*- coding: UTF-8 -*-
from mioji.common.ESlogger import RedisMQCostLogger
import time 
import json
import pika
import redis
import traceback
from mioji.common.logger import logger
from mioji.common.warning import warn
from mioji.common.func_log import cost_time
from mioji.common.conf_manage import get_local_ip

class CallbackWorkload(object):

    def __init__(self):
        self.pool_dict = dict()
    
    def __str__(self):
        return json.dumps(self.__dict__)

    def CallbackResult(self, spider=None, task=None, error_code=0, result_type="END"):
        """
        不只传spider进来是因为11错误码找不到spider
        @ task：任务task信息
        @ result_type：传入回调状态，end为最终状态同步执行，running为中间状态异步执行
        @ proxy：需要写入的回调数据
        @ error_code 写入的错误码
        """
        from slave import g_asy_callback_pool
        if result_type == "END":
            self.doCallback(task, error_code, spider, result_type)
        else:
            g_asy_callback_pool.spawn(self.doCallback, task, error_code, spider, result_type)

    def doCallback(self, task, error_code, spider, result_type):
        """
        执行回调工作
        """
        def get_ticket_num():
            ticket_num = 0
            for per_data_type in spider.crawl_targets_required:
                ticket_num += len(spider._asy_temp_result[per_data_type])
            return ticket_num

        def get_result(_result):
            _proxy_or_ticket = []
            for per_data_type in spider.crawl_targets_required:
                _proxy_or_ticket.extend(_result[per_data_type])
            return _proxy_or_ticket

        # 如果是 running状态 等一秒再判断下。
        if result_type == "RUNNING":
            num1 = get_ticket_num()
            time.sleep(1)
            # 缓冲后票张数量
            num2 = get_ticket_num()
            if num1 != num2 or spider.spider_frame_status:
                return

        task.other_info['parser_error'] = int(error_code)
        query = {"other_info": task.other_info}
        result = None
        redis_mq_logger = RedisMQCostLogger()
        extra = {}
        if spider:
            result = spider._asy_temp_result if result_type == 'RUNNING' else spider.result
            result = get_result(result)
            extra = spider.extra
            redis_mq_logger.ticket_num = len(spider._asy_temp_result)

        try:
            redis_mq_logger.qid = task.req_qid
            redis_mq_logger.source = task.source
            redis_mq_logger.task_id = task.new_task_id
            redis_mq_logger.task_info = task.content
            redis_mq_logger.error_code = error_code
            if result_type == 'END':
                redis_mq_logger.is_end = 1
            # 写入redis
            redis_cost = self.write_redis_ticket(task, result, error_code, extra)
            if isinstance(redis_cost, tuple):
                redis_mq_logger.conn_redis = redis_cost[0]
                redis_mq_logger.write_redis = redis_cost[1]
            else:
                redis_mq_logger.exception = redis_cost

        except Exception, e:
            logger.exception('not redis con' + str(e))
        # 写入mq
        operation_info = self.call_back_toservice(task, query, result_type)
        mq_try, mq_cost = operation_info.get('result', 0), operation_info.get('cost_time', 0)
        redis_mq_logger.mq_cost = mq_cost
        redis_mq_logger.mq_try = mq_try
        logger.debug('写入redis和mq：\n' + redis_mq_logger.logger_info)


    def write_redis_ticket(self, task, result, error_code, extra):
        try:
            begin = time.time()
            params = (task.redis_host, task.redis_port, int(task.redis_db), task.redis_passwd)
            rds = self.get_redis_pool(params)
            conn_cost_time = round(time.time() - begin, 3)
            # 等检索做兼容，暂时妥协方案，谷歌api返回格式强行转换。
            if task.source == "Realtraffic" and result:
                result = json.dumps(result[0])
            result = {"err_code": error_code, "data": result, "extra": extra}
            begin = time.time()
            if task.ticket_info.get("auth"):
                rds.setex(task.redis_key, json.dumps(result), 1800)
            else:
                rds.setex(task.redis_key, json.dumps(result), 600)
            write_cost_time = round(time.time() - begin, 3)
            return conn_cost_time, write_cost_time
        except Exception, e:
            warn_msg = 'redis_host:' + task.redis_host + ' ' + str(e)
            info = warn(task.req_qid, 'ex_SpiderRedis', msg=warn_msg)
            logger.exception("\n" + info)
            return str(e)

    def get_redis_pool(self, params):
        host, port, db, passwd = params
        redis_pool_key = (host, port, db, passwd)
        p = self.pool_dict.get(redis_pool_key, None)
        if p:
            coon = redis.Redis(connection_pool=p)
            return coon
        else:
            pool = redis.ConnectionPool(host=host, port=port, db=int(db), password=passwd)
            self.pool_dict[redis_pool_key] = pool
            coon = redis.Redis(connection_pool=pool)
            return coon

    @cost_time
    def call_back_toservice(self, task, query, spider_status):
        logger.debug('[callback a verifytask by rabbitmq]')

        def write_message(max_try):
            """
            :param max_try:
            :return:
            """
            try:
                max_try -= 1
                msg = json.dumps({
                    'qid': task.req_qid, 'type': task.callback_type,
                    'uid': task.req_uid, 'query': json.dumps(query),
                    'status': spider_status
                })
                credentials = pika.PlainCredentials(username=task.master_info['spider_mq_user']
                                                    , password=task.master_info['spider_mq_passwd'])
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=task.master_info['spider_mq_host'], virtual_host=task.master_info['spider_mq_vhost'], credentials=credentials,
                        # heartbeat_interval=0
                    )
                )
                channel = connection.channel()

                res = channel.basic_publish(
                    exchange=task.master_info['spider_mq_exchange'],
                    routing_key=task.master_info['spider_mq_routerKey'],
                    properties=pika.BasicProperties(delivery_mode=2),
                    body=msg,
                )
                connection.process_data_events()

                connection.close()
                if not res:
                    warn_msg = 'RabbitMQ Result False: {0}'.format(msg)
                    info = warn(str(task.req_qid), 'ex_RabbitMQ', get_local_ip(), warn_msg)
                    logger.debug("\n"+info)
                    raise Exception('RabbitMQ Result False')
                logger.debug('[callback a verifytask done] qid:{}, source: {}, task_info: {}, status: {}'.format(str(task.req_qid), str(task.source), task.content, spider_status))
                return max_try
            except Exception as exc:
                if max_try > 0:
                    return write_message(max_try)
                else:
                    warn_msg = 'RabbitMQ Result False qid : {}， e_info: {}, msg: {}'.format(task.req_qid, traceback.format_exc(), msg)
                    info = warn(task.req_qid, 'ex_SpiderMQ', get_local_ip(), warn_msg)
                    logger.exception("\n" + info)
                    return max_try

        _max_try = 3
        overage = write_message(_max_try)
        try_num = _max_try - overage
        return try_num

