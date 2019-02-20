#!/usr/bin/env python
#coding=UTF-8

import json 
import time 
import uuid
import urllib
import datetime
from mioji.common.logger import logger

TASK_DATE_FORMAT = '%Y%m%d'


class Task:
    """格式化抓取任务
    """
    def __init__(self, source='demo', content=None, extra={}):
        self.create_time = time.time()              # 任务被初始化的时间
        self.new_task_id = str(uuid.uuid1())        # 标识唯一任务
        self.task_type = False                      # 用于表示任务类型，api验证，ota验证， 非api和ota验证任务
        self.content = None
        self.source = None
        self.qid = None
        self.task_id = self.new_task_id
        self.tid = ""
        self.ori_type = ""
        self.ticket_info= dict()
        self.order_no = ""

    def __str__(self):
        return json.dumps(self.__dict__)
        
def creat_hotelParams(content):
    """
    酒店例行任务解析
    """
    _,adult,nights,check_in = content.split('&')
    rooms = [{'adult':int(adult)}]
    return HotelParams(value={'check_in': check_in, 'nights': int(nights), 'rooms': rooms})


class HotelParams(object):
    __slots__ = ('check_in', 'check_out', 'night', 'rooms_required', 'rooms_count', 'adult', 'child')

    def __init__(self, value={'check_in': '20170512', 'nights': 1, 'rooms': []}):
        self.check_in = datetime.datetime.strptime(value['check_in'], TASK_DATE_FORMAT)
        self.night = value.get('nights', 1)
        self.check_out = self.__init_check_out(self.check_in, self.night)
        self.rooms_count = 0
        self.adult = 0
        self.child = 0
        self.rooms_required = self.__init_rooms_required(value.get('rooms', []))
        self.__init_rooms_info()

    def __init_check_out(self, check_in, nights):
        return check_in + datetime.timedelta(days=nights)

    def __init_rooms_required(self, rooms):
        ps = []
        for r in rooms:
            ps.append(RequiredRoom(value=r))
        if not ps:
            ps.append(RequiredRoom())
        return ps

    def __init_rooms_info(self):
        for r in self.rooms_required:
            self.adult += r.adult
            self.child += r.child
            self.rooms_count += 1

    def format_check_in(self, ft):
        return self.check_in.strftime(ft)

    def format_check_out(self, ft):
        return self.check_out.strftime(ft)

class RequiredRoom(object):
    __slots__ = ('adult', 'child', 'child_age')

    def __init__(self, value={'adult': 2, 'child': 0, 'child_age': []}, default_child_age=6):
        self.adult = value.get('adult', 2)
        self.child = value.get('child', 0)
        self.child_age = value.get('child_age', [default_child_age] * self.child)


def ParseTask(req):
    """接收并解析task， 返回task对象list
    """
    result = list()
    params = req.params
    client_ip = req.remote_addr
    req_tasks = json.loads(urllib.unquote(params.get('req')))
    req_qid = params.get('qid')
    req_uid = params.get('uid')
    req_tid = params.get('tid', '')
    req_ori_type = params.get('ori_type', '')
    for req_task in req_tasks:
        try:
            task = Task()
            # 是否实时验证请求
            task.req_qid = req_qid
            task.req_uid = req_uid
            task.order_no = req_task.get('order_no', "")
            task.source = req_task.get('source')
            task.content = req_task.get('content')
            task.deadline = req_task.get('deadline', 0)
            task.debug = req_task.get('debug', False)
            task.tid = req_tid
            task.client_ip = client_ip
            task.ori_type = req_ori_type
            # task.proxy_info = proxy_info
            task.ticket_info = req_task.get('ticket_info')
            # todo 验证信息
            task.verify = req_task.get('verify', {'type': 'pre', 'set_type': 'E'})

            task.req_md5 = task.ticket_info.get('md5', 'default_md5')

            task.master_info = req_task.get('master_info', 'default_host')
            task.host = task.master_info.get('master_addr')

            task.redis_host = task.master_info.get('redis_addr').split(':')[0]
            task.redis_port = task.master_info.get('redis_addr').split(':')[-1]

            task.redis_db = task.master_info.get('redis_db')
            task.redis_passwd = task.master_info.get('redis_passwd')

            task.req_qid_md5 = task.req_qid + '-' + task.req_md5
            task.other_info = req_task.get('other_info', {})

            callback_type = 'scv100'
            if 'callback_type' in task.other_info:
                callback_type = task.other_info['callback_type']

            task.callback_type = callback_type

            redis_key_list = task.other_info.get('redis_key', [])
            # 之前redis_key 会传多个过来，现在只传一个，但保留了list的格式
            for each in redis_key_list:
                task.redis_key = each
                task.other_info['redis_key'] = each
                logger.info('s[{0}] id[{1}]new verify task:{2}'.format(task.source, task.new_task_id, task))
                result.append(task)
        except Exception, e:
            continue

    return result

