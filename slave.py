# -*- coding: utf-8 -*-
import gevent
from gevent import monkey, pywsgi
monkey.patch_all()
import zlib
import json
import sys
import time
import urllib
import uuid
import traceback
import bottle
import redis
import functools

# gevent 会限制get请求的长度, 改大小为20M
pywsgi.MAX_REQUEST_LINE = 1024 * 1024 * 20

from gevent.pywsgi import WSGIServer

import multiprocessing
from threading import Thread
sys.path.insert(0, "./lib/")
sys.path.insert(0, "./lib/mioji/common/")
from bottle import Bottle
from bottle import request as b_request
from gevent import sleep
from gevent.pool import Pool
from gevent.queue import Queue
from ucloud.ufile import multipartuploadufile
from ucloud.compact import BytesIO

from func_log import func_time_logger
from ESlogger import ExceptionLogger, ErrorCodeLogger
from spider_factory import SpiderFactory
from mioji.common.utils import get_md5, current_log_tag
from mioji.common.logger import logger
from mioji.common.task_info import Task, ParseTask
from mioji.common.conf_manage import g_config
from mioji.common.callback import CallbackWorkload
from mioji.common.common import get_proxy
from mioji.common.common import check_all_result
from mioji.common.parser_except import ParserException, SLAVE_ERROR
from mioji.common.warning import warn

from mioji.common import spider
# 装配代理
spider.slave_get_proxy = get_proxy


callback = CallbackWorkload()

# 处理task的协程池
g_co_pool = Pool(g_config.co_pool_size)
# 监听线程收到的任务队列
g_task_queue = Queue(g_config.task_queue_size)
# 爬虫抓取任务以外的异步任务队列 （如写日志原文到对象存储）
g_task_post_process_queue = Queue(g_config.process_queue_size)
# 处理post process task的协程池
g_post_process_co_pool = Pool(g_config.co_pool_size)
# Spider工厂对象
g_spider_factory = SpiderFactory()
# 异步回调的协程池
g_asy_callback_pool = Pool(g_config.target_async_size)
# 监听任务子进程队列
g_multi_queue = multiprocessing.Queue()

#任务线程
class Worker(Thread):
    def run(self):
        while True:
            spider_task = g_task_queue.get(block=True)
            logger.info('协程池大小: {0} 协程池空闲: {1}'.format(g_co_pool.size, g_co_pool.free_count()))
            if g_co_pool.free_count() < 2:
                msg = "协程池中任务堆积:{} 空闲池:{} 任务池:{}".format(g_co_pool.size,g_co_pool.free_count(),
                                                           g_task_queue.qsize())
                print
                callback.CallbackResult(task=spider_task, error_code=98, result_type="END")
                logger.debug("\n" + warn(qid=spider_task.req_qid, type="ex1002", msg="爬虫队列满了"))
            else:
                g_co_pool.spawn(doTask, spider_task)


#心跳线程
class Heartbeat(Thread):
    def run(self):
        while True:
            print "写入心跳"
            info = "%s:%d_%s" % (g_config.local_ip, g_config.local_port, g_config.env)
            heart_beat_redis = redis.Redis(host=g_config.heart_beat_redis_host, port=g_config.heart_beat_redis_port,
                                 password=g_config.heart_beat_redis_pwd, db=g_config.heart_beat_redis_db)
            heart_beat_redis.set(info,1,g_config.heart_beat_interval)
            if g_config.env == "Test":
                info_test1 = "%s:%d_%s" % (g_config.local_ip, g_config.local_port, "Test1")
                heart_beat_redis.set(info_test1,1,g_config.heart_beat_interval)
            sleep(g_config.heart_beat_interval)

#异步写抓取原文线程
class PostProcessWorker(Thread):
    def run(self):
        while True:
            res, task, md5_key = g_task_post_process_queue.get(block=True)
            g_post_process_co_pool.spawn(doPostProcessTask,res, task, md5_key )


#后处理主处理函数
@func_time_logger
def doPostProcessTask(res, task, key):
    
    logger.debug(current_log_tag() + '[验证页面开始上传]')

    handler = multipartuploadufile.MultipartUploadUFile(g_config.ucloud_public_key, g_config.ucloud_private_key)
    stream = BytesIO(zlib.compress(res))
    ret, resp = handler.uploadstream(g_config.ucloud_bucket, key, stream)
    # 出问题重试 2 次
    retry_times = 2
    if resp.status_code == 200:
        logger.debug(current_log_tag() + '[验证页面上传结束] md5:{0}'.format(key))
        return True
    while resp.status_code != 200 and retry_times:
        retry_times -= 1
        ret, resp = handler.resumeuploadstream()
        if resp.status_code == 200:
            logger.debug(current_log_tag() + '[验证页面上传结束] md5:{0}'.format(key))
            return True
    else:   
        except_logger = ExceptionLogger()
        except_logger.qid = task.req_qid
        except_logger.type = "PUSH_MD5_ERROR"
        except_logger.debug = json.dumps({"task_id": task.new_task_id, "source": task.source})
        logger.debug("\n" + except_logger.logger_info)
        logger.debug(current_log_tag() + '[验证页面上传失败] md5:{0}'.format(key))

        return False

    

#协程任务主处理函数
def doTask(task):
    """ 此方法用于调用spider 并接收最终的code和result信息
    """
    spider = g_spider_factory.get_spider(task.source)
    if not spider :
        logger.error('未找到指定源[%s]对应的spider' % (task.source))
        callback.CallbackResult(task=task, error_code=11,result_type="END")
        code = 11
    else:
        spider = spider(task)
        spider.task = task
        print task
        spider.debug = False
        spider.process_callback = callback.CallbackResult  # 执行回调
        spider.task_post_process_queue = g_task_post_process_queue # 上传ucloud所用池子
        spider.need_proxy =  g_config.need_proxy 
        spider.machine_type = g_config.machine_type
        spider.env = g_config.env
        spider.local_ip = g_config.local_ip
        spider.is_verify = g_config.need_post_process
        crawl_time = time.time()
        try:
            spider = spider_crawl(spider, task) # 执行 爬虫，并从头重试
        except ParserException as e:
            error_info = e.msg
            error = e.code
            logger.exception('新框架 爬虫抛出异常: task:{0}, error:{1}, msg: {2}'.format(task, error_info, error))
        except Exception, e:
            logger.exception("新框架 爬虫抛出异常: task_data:{0}  error:{1}".format(task, e))
            error = SLAVE_ERROR
        spider.last_time = int((time.time() - crawl_time) * 1000)
        check_all_result(spider) # 最后对所有返回数据进行check 
        spider.spider_frame_status = 1
        callback.CallbackResult(task=task, error_code=spider.code, spider=spider, result_type="END") # 执行回调操作，如果是end将执行同步回调
        error_logger(spider) # 写入error日志

        code = spider.code
    logger.info("[爬虫反馈 code: {0}][source: {1}] task: {2}".format(code, task.source, task))


def error_logger(spider):
    if hasattr(spider.task, 'new_task_id'):
        cur_id = spider.task.new_task_id
    else:
        cur_id = str(uuid.uuid1())
    
    task_id = cur_id
    if hasattr(spider, "succeed_pages"):
        spider.error_code_logger.succeed_pages = spider.succeed_pages
    elif hasattr(spider, "success_count"):
        spider.error_code_logger.succeed_pages = spider.success_count
    if hasattr(spider, "total_crawl_pages"):
        spider.error_code_logger.total_crawl_pages = spider.total_crawl_pages
    elif hasattr(spider, "all_count"):
        spider.error_code_logger.total_crawl_pages = spider.all_count

    if hasattr(spider.task, "verify"):
        verify_type = spider.task.verify
        if isinstance(verify_type, dict):
            _type = verify_type.get('type', "")
        else:
            verify_type = json.loads(spider.task.verify)
            _type = verify_type.get('type', "")
        spider.error_code_logger.verify_type = _type
    spider.error_code_logger.task_id = cur_id
    spider.error_code_logger.source = spider.task.source
    spider.error_code_logger.tid = spider.task.tid
    spider.error_code_logger.ori_type = spider.task.ori_type
    spider.error_code_logger.task_info = json.dumps(spider.task.ticket_info, ensure_ascii=False)
    spider.error_code_logger.content = spider.task.content
    spider.error_code_logger.client_ip = spider.task.client_ip
    spider.error_code_logger.error_code = convert_code(spider.code)
    spider.error_code_logger.detail_code = spider.code
    spider.error_code_logger.qid = spider.task.req_qid
    spider.error_code_logger.MD5 = spider.verify_data["data"]
    spider.error_code_logger.last_time = spider.last_time
    if spider.code != 0:
        spider.error_code_logger.exception = spider.exception
    logger.debug('\n' + spider.error_code_logger.logger_info)

def retry_by_deadline(func):
    # 在指定时间内的无限重试
    @functools.wraps(func)
    def wapper(*args, **kwargs):
        parser, task = args
        deadline = task.deadline
        try:
            max_try = parser.retry_info.get('max_try', 1)
            retry_codes = parser.retry_info.get('retry_codes', [])
        except:
            max_try = 1
            retry_codes = []
        retry_codes.extend([22, 23, 24, 36, 37])
        max_try = 100
        begin = time.time()
        for i in range(max_try):
            # 剩余重试次数
            remaining_times = max_try - i
            logger.info('retry_by_deadline开始')
            parser = func(parser, task)
            # 错误码在可重试码内 && 当前运行时间<deadline && 当前运行次数 < 爬虫最大重试次数
            if parser.code in retry_codes and (time.time() - begin < deadline) and remaining_times > 1:
                # 重试 保持相同的task_id, 开始抓取时间, 接收第一次的抓取结果
                parser = update_parser_from_older(parser, task, True)
                continue
            else:
                break
        # 爬虫任务级日志记录
        if parser.code == 0:
            parser.error_code_logger.exception = ''
        logger.info('retry_by_deadline结束')
        return parser
    return wapper

def update_parser_from_older(_old_parser, task, need_result=False):
    parser = _old_parser
    parser.task_id = _old_parser.task_id
    parser.start_crawl_time = _old_parser.start_crawl_time
    if need_result:
        parser._result = _old_parser._result
        parser._asy_temp_result = _old_parser._asy_temp_result
        parser.error_code_logger = _old_parser.error_code_logger
        parser.error_code_logger.retry_times += 1

    logger.info('update_parser success')
    return parser

@retry_by_deadline
def spider_crawl(spider, task):
    """
    重头开始重试
    :param parser:
    :param task:
    :return:
    """
    retry_count = 0
    need_crawl = True

    while need_crawl:
        retry_count += 1
        try:
            spider.error_code_logger = ErrorCodeLogger()
            spider.crawl()
            return spider
        except ParserException as e:
            need_crawl = retry_count < e.retry_from_first_count
            if not need_crawl:
                raise e
            else:
                # 重试 保持相同的task_id, 开始抓取时间
                spider = update_parser_from_older(spider, task)
                spider.error_code_logger.retry_times += 1
                logger.debug('retry from first - {0}/{1}'.format(retry_count, e.retry_from_first_count))


def convert_code(code):
    if str(code).startswith("22"):
        return 22
    elif str(code).startswith("12"):
        return 12
    elif str(code).startswith("29"):
        return 29
    else:
        return int(code)

web_app = Bottle()

def do_worker(task_info_list):
    ''' 
    1、接收web请求
    2、检查并解析task
    3、一个请求中可能有多个任务，将任务依次添加进worker中
    4、接收任务时检查任务队列长度，如超过，同步回调中返回错误信息。使检索重发任务（假设负载均衡做的不好）
    
    '''
    bottle_r_time_0 = time.time()

    task_num = len(task_info_list)
    req_num = g_task_queue.qsize() + task_num
    bottle_r_time_1 = time.time() - bottle_r_time_0
    for task in task_info_list:
        try:
            g_task_queue.put(task)
        except:
            # 任务队列已满
            traceback.format_exc()
            callback.CallbackResult(task=task, error_code=98, result_type="END")
            logger.debug("\n" + warn(qid=task.req_qid, type="ex1002", msg="爬虫队列满了"))
    bottle_r_time_2 = time.time() - bottle_r_time_0
    logger.info("bottle_run_time: 解析task: {}秒，总耗时：{}秒".format(bottle_r_time_1, bottle_r_time_2))
    

@web_app.get("/rtquery")
@web_app.post("/rtquery")
def Request():
    result = {'result': '0','task': []}
    task_info_list = ParseTask(b_request)
    g_multi_queue.put(task_info_list)
    for i in task_info_list:
        result['task'].append({'err_code': '0'})
    return json.dumps(result)

    

def WSGI():
    server = WSGIServer(('0.0.0.0', g_config.local_port), web_app)
    server.serve_forever()
    

if __name__ == "__main__":
    
    # 所属环境 通过start脚本传进来
    try:
        g_config.local_port = int(sys.argv[1]) # 进程端口
        g_config.env = sys.argv[2] # 机器环境
        g_config.machine_type = sys.argv[3] # 机器类型 
    except:
        print "默认使用 test环境 verfiy 机器类型"
        g_config.env = "local"
        g_config.machine_type = "verify"
        g_config.local_port = 8089

    if g_config.env in [ "newverify", "webdrive"]:
        g_config.need_proxy = True
    if g_config.machine_type in [ "newverify", "webdrive", "real", "api"]:
        g_config.need_post_process = True

    # 根据环境获取，取代理地址
    g_config.get_proxy_host()
    
    #初始化Spider工厂对象
    g_spider_factory.load()

    #启动爬虫任务处理线程
    Worker().start()

    #使用子进程启动Web监听服务
    mut = multiprocessing.Process(target=WSGI)
    mut.start()

    # if g_config.env == "local":
    #   本地启动，不需要心跳和上传
    
    # 启动异步写上传原文线程
    PostProcessWorker().start()
    # 保证前面准备完毕
    time.sleep(1)
    #启动心跳线程
    Heartbeat().start()

    while True:
        if not g_multi_queue.empty():
            task_info_list = g_multi_queue.get()
            do_worker(task_info_list)
        else:
            gevent.sleep(10)
