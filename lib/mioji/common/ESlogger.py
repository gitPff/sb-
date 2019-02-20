#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @Time    : 2018/5/22 下午5:15
# @Author  : Fan bowen
# @Site    : 
# @File    : ESlogger.py
# @Software: PyCharm

from datetime import datetime as dt
import json
import pytz

import socket
import chardet



def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception as why:
        ip = str(why)
    finally:
        s.close()

    return ip


class BaseEsLogger(object):
    def __init__(self):
        self.qid = ""
        self.source = ""
        self.task_id = ""
        self.exception = ""
        tz = pytz.timezone(u'Asia/Shanghai')
        self.t = dt.now(tz=tz).strftime("%Y-%m-%dT%H:%M:%S+08:00")
        if isinstance(self.t, tuple):
            self.t = self.t[0]
        self.ori_ip = get_host_ip()

    def get_host_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception as why:
            ip = str(why)
        finally:
            s.close()

        return ip

    @property
    def logger_info(self):
        if 'resp_content' in self.__dict__:
            info = self.__dict__
            resp_coding = chardet.detect(self.resp_content)['encoding']
            info["resp_content"] = unicode(info["resp_content"],errors='ignore')
            return json.dumps(info, encoding=resp_coding).replace("\n", "$$n")
        else:
            return json.dumps(self.__dict__).replace("\n", "$$n")


class ErrorCodeLogger(BaseEsLogger):
    def __init__(self):
        super(ErrorCodeLogger, self).__init__()
        self.log_type = "error_code"
        self.error_code = -1
        self.detail_code = -1
        self.task_info = ""
        self.exception = ""
        self.last_time = ""
        self.total_crawl_pages = -1
        self.succeed_pages = -1
        self.verify_type = ""
        self.content = ""
        self.tid = ""
        self.ori_type = ""
        self.retry_times = 0
        self.key = "MJ_MD_SP_ERROR_LOG"
        self.MD5 = ""


class HttpLogger(BaseEsLogger):
    def __init__(self):
        super(HttpLogger, self).__init__()
        self.log_type = "http"
        self.req_type = ""
        self.url = ""
        self.data = ""
        self.cookie = ""
        self.headers = ""
        self.proxy = ""
        self.proxy_out = ""
        self.resp_code = -1
        self.last_time = ""
        self.proxy_inf = ""
        self.retry_count = ""
        self.tid = ""
        self.ori_type = ""
        self.key = "MJ_MD_SP_HTTP_LOG"


class RedisMQCostLogger(BaseEsLogger):
    def __init__(self):
        super(RedisMQCostLogger, self).__init__()
        self.log_type = "redis_mq_cost"
        self.error_code = -1
        self.task_info = ""
        self.conn_redis = -1        # 连接redis耗时
        self.write_redis = -1       # 写redis耗时
        self.mq_cost = -1           # mq耗时(连接+写入)
        self.mq_try = -1            # mq连接次数
        self.ticket_num = 0         # 票数量
        self.is_end = 0             # 爬虫状态 0: RUNNING 1: END
        self.key = "MJ_MD_SP_RDMQ_LOG"



class ExceptionLogger(object):
    def __init__(self):
        self.debug = "{}"
        self.qid = None
        self.type = ""
        self.key = "MJ_MD_STATS_LOG"

    @property
    def logger_info(self):
        return json.dumps(self.__dict__).replace("\n", "$$n")




if __name__ == "__main__":
    # ex = ExceptionLogger()
    # ex.resp = "1"
    # ex.key = "name"
    # ex.resp = "xi"
    # print ex.logger_info
    # a = ErrorCodeLogger()
    # print a.__dict__
    # print a.logger_info
    b = HttpLogger()
    b.content = {"a": 1}
    print b.logger_info

    # import socket
    #
    #
    # def get_host_ip():
    #     try:
    #         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #         s.connect(('8.8.8.8', 80))
    #         ip = s.getsockname()[0]
    #     finally:
    #         s.close()
    #
    #     return ip
    # print get_host_ip()
