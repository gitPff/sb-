#!/usr/bin/python
# -*- coding: UTF-8 -*-
# @Time    : 2018/6/5 下午4:14
# @Author  : Fan bowen
# @Site    : 
# @File    : warning.py
# @Software: PyCharm
import json
from datetime import datetime as dt
import socket

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
            local_ip = res
        except Exception:
            pass
    return local_ip

def warn(qid, type, ori_ip=getLocalIp(), msg=None):
    return_json = {
            "key": "MJ_MD_EX_LOG",
            "qid": qid,
            "type": type,
            "t": dt.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "ori_ip":ori_ip,
            "msg": msg,
        }
    return json.dumps(return_json, ensure_ascii=False)


if __name__ == "__main__":
    pass