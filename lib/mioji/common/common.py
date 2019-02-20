#!/usr/bin/env python
# coding=UTF-8
'''
    Created on 2014-03-22
    @author: devin
    @desc:

'''
import socket
import json
import requests
import traceback
from logger import logger
from conf_manage import g_config
from mioji.common.task_info import Task
from mioji.common import parser_except
import MySQLdb
from mioji.common.warning import warn
import time


# new_proxy_host = '10.10.182.238:9090'

local_ip = None

def getLocalIp():
    global local_ip
    if local_ip:
        return local_ip
    else:
        res = ''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            res = s.getsockname()[0]
            s.close()
        except Exception:
            pass
        local_ip = res
    return local_ip


ip = getLocalIp()


def set_proxy_client(client):
    global proxy_client2
    proxy_client2 = client


def get_proxy(source=None, allow_ports=[], forbid_ports=[],
              allow_regions=[], forbid_regions=[], user='realtime', passwd='realtime', proxy_info={},
              verify_info="verify", ip_num=1, ip_type="internal", task=Task(), ):
    """
    全都需要取代理暂时
    """

    qid = str(task.ticket_info.get('qid', int(time.time()*1000)))

    msg = {"req": [{
        "source": source,
        "type": verify_info,
        "num": ip_num,
        "ip_type": ip_type,
    }]}
    msg = json.dumps(msg)
    ptid = task.ticket_info.get('ptid', "")
    time_st = time.time()
    get_info = '/?type=px001&qid={0}&query={1}&ptid={2}&tid=tid&ccy=AUD'.format(qid, msg, ptid)
    logger.info("get proxy info :http://{1}{0}".format(get_info, g_config.proxy_host))
    count = 1
    while 1:
        try:
            p = requests.get("http://{0}".format(g_config.proxy_host)+get_info, timeout=(6, 6), stream=False)
            p_time = p.elapsed.total_seconds()
            p = p.content
            logger.info("代理返回内容为{0}".format(p))
            proxy_ip = json.loads(p)['resp'][0]['ips'][0]['inner_ip']
            break
        except:
            exstr = traceback.format_exc()
            msg = '取代理请求时报错，错误信息为：' + exstr
            info = warn(qid, 'ex_GetProxyFail', ip, msg)
            logger.debug("\n" + info)
            if count == 3 :
                raise parser_except.ParserException(21, "取代理时失败")
            time.sleep(3)
            logger.debug("取代理失败，进行第{}次重试,".format(count))
            count += 1
    time_end = time.time() - time_st
    # 代理服务有时候会返回一个只有":"的代理！
    if len(proxy_ip) < 9:
        msg = "获取到的代理不可用！"
        info = warn(qid,'ex_GetProxyFail', ip, msg)
        logger.debug("\n" + info)
        raise parser_except.ParserException(21, "获取到的代理有误：{}".format(p))
    if not proxy_ip:
        msg = '未获取到代理，请求信息为：'+ get_info
        info = warn(qid,'ex_GetProxyFail', ip, msg)
        logger.debug("\n" + info)
        raise parser_except.ParserException(21, "未获取到代理")
    if p_time > 1.5:
        msg = '获取代理成功耗时， 耗时：{0}, requests 记录超时时间：{1}'.format(time_end, p_time)
        info = warn(qid,'ex_GetProxyFail', ip, msg)
        logger.debug("\n"+info)
    p = [proxy_ip, [p, time_end, get_info]]
    return p

def check_all_result(spider):
    if spider.code == 0:
        # 默认通过数据状况判断 29
        if not spider.result:
            spider.code = 29

        for k, v in spider.result.items():
            if not v:
                spider.code = 29

    if spider.code == 29:
        if spider.result:
            for k, v in spider.result.items():
                if v:
                    spider.code = 36





if __name__ == '__main__':
    # p = get_proxy(forbid_regions=['CN'])
    # cand_str = 'test str'
    # print getStrMd5(cand_str)
    # print proxy_ips
    # print getLocalIp()
    # print getLocalIp()
    # print getLocalIp() not in proxy_ips
    from gevent import monkey
    monkey.patch_all()
    import gevent
    #
    ip = '10.10.95.70'
    # print(get_proxy())
    gevent.joinall([gevent.spawn(get_proxy, source) for source in range(3)])
    # print(get_conn("select inner_ip from spider_verify_machine WHERE type = 'routine'"))