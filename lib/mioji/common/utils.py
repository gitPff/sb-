#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

import re, requests
# import httplib
import hashlib
import socket
import json
from greenlet import getcurrent


host = 'http://10.10.239.46:8087'


def current_log_tag():
    g = getcurrent()
    tag = 'None,None,'
    if hasattr(g, 'spider_taskinfo'):
        taskinfo = g.spider_taskinfo
        tag = '{0},{1} '.format(taskinfo.get('source',None), taskinfo.get('task_id',None))
    return tag


def simple_get_socks_proxy_new(source='',task='',ip_type='',ip_num='',verify_info=''):
    proxy_info = requests.get("http://10.10.239.46:9090/?type=px001&qid=0&query={%22req%22:%20[{%22source%22:%20%22ctripFlight%22,%20%22num%22:%201,%20%22type%22:%20%22verify%22,%20%22ip_type%22:%20%22test%22}]}&ptid=test&uid=test&tid=tid&ccy=spider_test").content
    proxy = json.loads(proxy_info)['resp'][0]['ips'][0]['inner_ip']
    external_ip = json.loads(proxy_info)['resp'][0]['ips'][0]['external_ip']
    return [proxy, [proxy_info, '1'], external_ip]

def setdefaultencoding_utf8():
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')

def get_md5(src):
    return hashlib.md5(src).hexdigest()

def get_local_ip():
    import socket
    res = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        res = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return res

def remove_html_tags(src):
    r = re.sub(r'</?\w+[^>]*>', '', src)
    return r

def creat_hotelParams(content):
    """
    酒店例行任务解析
    """
    _,adult,nights,check_in = content.split('&')
    rooms = [{'adult':int(adult)}]
    return HotelParams(value={'check_in': check_in, 'nights': int(nights), 'rooms': rooms})

