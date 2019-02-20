#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月19日

@author: dujun
'''
import os
import copy
from logger import logger
import json as _json
import requests, httplib, time
from func_log import func_time_logger
from user_agent_list import random_useragent, new_header
from utils import current_log_tag
import traceback
from spider_queue_qps import queue_and_qps
import gevent
from ESlogger import HttpLogger

import parser_except
from frequency_limit import default_limiter, limit_config


SOCKS_PROXY = '10.10.7.155|10.10.239.141|10.10.214.26|10.10.120.163|10.10.128.62|10.10.137.138|10.10.119.18|10.10.'
DJUserAgent = 'User-agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'


class MechanizeCrawler(object):
    def __init__(self, referer='', headers=None, p='', md5='', qid='', **kw):

        self.proxy = p
        self.md5 = md5
        self.qid = qid
        self.task_id = kw.get("task_id", "")
        self.source = kw.get("source", "")
        if not headers:
            headers = {}
        self.headers = headers
        requests.adapters.DEFAULT_RETRIES = 5
        self.br = requests.Session()
        self.br.keep_alive = False
        self.Userproxy = False
        headers['User-agent'] = new_header()
        # headers['Connection'] = 'keep-alive'
        self.br.headers.update(headers)
        self.resp = None
        self.real_ip = None
        self.out_ip = ""
        self.proxy_inf = ""
        self.req_count = 0
        self.tid = ""
        self.ori_type = ""
        if p:
            self.set_proxy(p)

        self.req_bind = {'get': self.br.get, 'post': self.br.post, 'head': self.br.head, 'put': self.br.put,
                         'delete': self.br.delete}
        self.queue_info = {}

    @staticmethod
    def del_user_ua(d):
        if 'User-agent' in d:
            del d['User-agent']
        if 'user-agent' in d:
            del d['user-agent']

    @staticmethod
    def set_debug(flag=False):
        if flag:
            httplib.HTTPConnection.debuglevel = 1
            httplib.HTTPSConnection.debuglevel = 1

    @func_time_logger
    def req(self, url, method='get', params=None, data=None, json=None, timeout=60, verify=False, **kw):
        httpLogger = HttpLogger()
        httpLogger = copy.deepcopy(httpLogger)
        httpLogger.qid = self.qid
        httpLogger.task_id = self.task_id
        httpLogger.req_type = method
        httpLogger.source = self.source
        httpLogger.task_id = self.task_id
        httpLogger.qid = self.qid
        httpLogger.url = url
        httpLogger.proxy_out = str(self.out_ip)
        httpLogger.proxy = str(self.proxy)
        httpLogger.proxy_inf = str(self.proxy_inf)
        httpLogger.retry_count = self.req_count
        for k in kw.keys():
            if k not in ['method', 'url', 'params', 'data', 'headers', 'cookies', 'files', 'auth', 'timeout',
                         'allow_redirects', 'proxies',
                         'hooks', 'stream', 'verify', 'cert', 'json']:
                logger.warning(current_log_tag() + '[出现不能解析的 req 请求参数][{0}]'.format(k))
        new_kw = {k: v for k, v in kw.items() if
                  k in ['method', 'url', 'params', 'data', 'headers', 'cookies', 'files', 'auth', 'timeout',
                        'allow_redirects', 'proxies',
                        'hooks', 'stream', 'verify', 'cert', 'json']}
        ts = int(1000 * time.time())
        if data:
            httpLogger.data = data
            if isinstance(data, dict):
                httpLogger.data = _json.dumps(data, ensure_ascii=False)
        if json:
            httpLogger.data = json
            if isinstance(json, dict):
                httpLogger.data = _json.dumps(json, ensure_ascii=False)
                
        req_func = self.req_bind.get(method.lower())
        httpLogger.cookie = str(req_func.im_self.cookies._cookies)
        httpLogger.source = self.source
        httpLogger.headers = str(new_kw.get('headers', ""))
        try:
            logger.debug(current_log_tag() + 'browser req start {1} {0}'.format(url, method))
            logger.debug(current_log_tag() + 'browser req data {0}'.format(data))
            logger.debug(current_log_tag() + 'browser req json {0}'.format(json))
            logger.debug(current_log_tag() + 'browser req other_data {0}'.format(new_kw))
            logger.debug(current_log_tag() + 'browser req session_cookie {0}'.format(req_func.im_self.cookies._cookies))
        except:
            logger.debug(current_log_tag() + '请求前获取部分参数失败')
        try:
            local_resp = None
            try:
                logger.debug(current_log_tag() + 'queue and qps config:{0}'.format(str(self.queue_info)))
                if self.queue_info['source_name'] in limit_config.keys():
                    logger.debug(current_log_tag() + 'new queue and qps')
                    if self.new_queue():
                        pass
                    else:
                        raise parser_except.ParserException(parser_except.NEW_QPS_OVERFLOW, msg='排队超时')
                elif self.queue_info:
                    while True:
                        res = queue_and_qps(self.queue_info)
                        logger.debug(current_log_tag() + 'queue and qps response:{0}'.format(str(res)))
                        if res:
                            break
                        elif res is not None:
                            gevent.sleep(0.0001)
                            continue
                        else:
                            # TODO (范博文) 此处应该添加报警方式

                            break
            except Exception as why:

                logger.debug(current_log_tag() + 'queue and qps fail reason:{0}'.format(str(why)))
            self.resp = local_resp = req_func(url, params=params, data=data, json=json, timeout=timeout, verify=verify, **new_kw)
            logger.debug(current_log_tag() + 'browser response headers:{0}'.format(self.resp.headers))
            ts = int(1000 * time.time()) - ts
            httpLogger.last_time = ts
            logger.debug(current_log_tag() + 'browser req end {1} {0} proxy[{4}] ms[{2}] status[{3}] length[{5}]'
                         .format(url, method, ts, local_resp.status_code, self.proxy, resp_content_lenght(local_resp)))
            httpLogger.resp_code = local_resp.status_code
            if len(str(local_resp.content)) > 1000:
                content = str(local_resp.content)[:1000]
            else:
                content = str(local_resp.content)
            httpLogger.resp_content = content
            httpLogger.proxy_out = str(self.out_ip)
            httpLogger.proxy = str(self.proxy)
        except:
            httpLogger.exception = str(traceback.format_exc())
            logger.debug(current_log_tag() + 'browser req end {1} {0} proxy[{2}] error:{3}'.format(url, method, self.proxy, traceback.format_exc()))
            try:
                logger.debug('\n' + httpLogger.logger_info)
            except Exception as why:
                logger.debug(str(why))
            raise
        try:
            logger.debug('\n' + httpLogger.logger_info)
        except Exception as why:
            logger.debug(str(why))
        return local_resp

    def set_proxy(self, p, https=False):
        self.proxy = p
        proxy_type = 'NULL'
        if p is not None and p != "REALTIME":
            # socks都是内网socks服务转发，所以以 10. 开头判断
            if "PROXY_API" in p:
                proxy_type = "API"
                self.br.proxies = p["PROXY_API"]
            elif "PROXY_GOOGLE_MAPS" in p:
                proxy_type = "GOOGLE_MAPS"
                self.br.proxies = p["PROXY_GOOGLE_MAPS"]
            
            elif p.startswith('10.'):
                # if p.split(':')[0] in SOCKS_PROXY:
                proxy_type = 'socks'
                self.br.proxies = {
                    'http': 'socks5://' + p,
                    'https': 'socks5://' + p
                }
                try:
                    # self.real_ip = get_real_id(self.br.proxies)
                    self.real_ip = p
                except Exception:
                    pass
            else:
                self.real_ip = p.split(':')[0]
                proxy_type = 'http'
                self.br.proxies = {
                    'https': 'http://' + p,
                    'http': 'http://' + p,
                }
        logger.debug('[框架设置代理][代理类型: %s][代理 ip: %s ]' % (proxy_type, p))

    def get_proxy(self):
        return self.proxy

    def get_session(self):
        return self.br

    def close(self):
        self.br.close()

    def get_cookie_str(self):
        return self.resp.cookies

    def add_cookie(self, cookie={}):
        self.br.cookies.update(cookie)

    def get_response(self):
        self.resp.code = self.resp.status_code
        return self.resp

    def add_referer(self, url):
        self.br.headers.update({'Referer': url})

    def add_header(self, headers={}, use_header=False):
        self.del_user_ua(headers)
        if use_header:
            headers = {'User-agent': new_header()}
        return self.br.headers.update(headers)

    def get_cookie_handle(self):
        pass

    def get_cookie(self, method, url_base, paras={}, paras_type=1, **kw):
        page, _ = self.req(method, url_base, paras={}, paras_type=1, **kw)
        dcookie = requests.utils.dict_from_cookiejar(self.resp.cookies)
        return dcookie, _

    def get_url(self, method, url_base, paras={}, paras_type=1, **kw):
        page, _error = self.req(method, url_base, paras={}, paras_type=1, **kw)
        return self.get_url_of_response(), _error

    def new_queue(self):
        """
        触发新的排队
        :return:
        """
        try:
            with default_limiter.dblock_wait(self.queue_info['source_name'], {'task_id': self.task_id}, timeout=50) as _:
                return True
        except Exception as why:
            logger.debug('new queue and qps error' + str(why))
            return False




def resp_content_lenght(resp):
    return 0 if resp is None else len(resp.content)


def wrap_req(mc, func, args, **kw):
    return func(args, **kw)

def curl_real_ip(p):
    try:
        time_1 = time.time()
        socks_req = '''curl --socks5 {1} http://httpbin.org/ip'''.format(p)
        socks_IP = os.popen(socks_req).readlines()
        logger.debug('[框架设置代理][socks代理出口 ip: %s ]' % (socks_IP))
        time_2 = time.time()
        socks_time = time_2 - time_1 
        logger.debug('[获取socks代理出口ip，耗时 %s 秒]' % (socks_IP))
    except Exception:
        logger.error(' ')
        pass

def get_real_id(proxy):
    url = 'http://httpbin.org/get'
    res = requests.get(url, proxies=proxy)
    return json.loads(res.content)['origin']


if __name__ == '__main__':
    mc = MechanizeCrawler()
    url = 'https://www.expedia.com.hk/Flights-Search?trip=oneway&passengers=children:0,adults:1,seniors:0,infantinlap:Y&mode=search&leg1=from:北京,to:巴黎,departure:2017/02/16TANYT'
    url = 'https://www.expedia.com.hk/Flights-Search?trip=oneway&passengers=children:0,adults:1,seniors:0,infantinlap:Y&mode=search&leg1=from:\xe5\x8c\x97\xe4\xba\xac,to:\xe5\xb7\xb4\xe9\xbb\x8e,departure:2017/02/16TANYT'
    url = 'https://www.expedia.com.hk/Hotel-Search?&langid=2052'
    req = {'url': url}
    print mc.req(url,
                 header={}, asdfasdf={}).content