#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @author: focus
# encoding: utf-8
import json
import time
import functools
from mioji.common.logger import logger
from datetime import datetime
from pymongo import MongoClient

__auth__ = 'fan bowen'

'''新的查订比文件涵盖了search到booking再到cancel等所有接口的请求次数，按照每个不同的接口类型以及它们的成功失败状态整理归类写入到mongo，统计出各个接口的使用次数以及状态'''


de_module = {
    "jacApi": "JacApi",
    "zailushangApi": "IBEApi",
    "travelzenApi": "TravelzenApi",
    "yinlingApi": "YinlingApi",
    "touricoApi": "TouricoApi",
    "igolaApi": "IgolaApi",
    "daolvApi": "DaolvApi",
    "meiyaApi": "MeiyaApi",
    "mikiApi": "MikiApi",
    "gtaApi": "GTAApi",
    "pkfareApi": "PkfareApi",
    "huizucheApi": "HuizucheApi",
    "dotwApi": "DotwApi",
    "huangbaocheAPi": "HuangbaocheApi",
    "huizucheAPi": "HuizucheApi",
    "hotelbedsApi": "HotelBedsApi",
    "huantaoyouApi": "HuantaoyouApi",
    "expediaTaapApi": "ExpediaTaapApi",
    "51bookApi": "book51Api",
    "raileuropeApi": "raileuropeApi",
    "raileuropeDBApi": "raileuropeApi",
    "raileuropeATOCApi": "raileuropeApi",
    "raileuropeRENFEApi": "raileuropeApi",
    "zuzucheApi": "ZuzucheApi",
    "hotelsproApi": "HotelsproApi",
    "jielvApi": "JLTourApi",
    "fliggyApi": "FliggyApi",
    "tongchengApi": "tongChengApi",
    "veturisApi": "VeturisApi",
    "aicApi": "AicApi",
    "travcoApi": "TravcoApi",
    "jtbApi": "JtbApi",
    "eanApi": "EanApi",
    "mgApi": "MgApi",
    "tangrenjieApi": "TangrenjieApi",
    "tuniuApi": "TuniuApi",
    "tongchengCNApi": "TongChengCNApi",
    "nuiTeeApi": "NuiTeeApi",
    "flightroutesApi": "FlightroutesApi",
    "QunarApi":"qunarApi",
}

class CheckBookRatio(object):
    def __init__(self, **kwargs):
        pass
    def insert_record_qid(self):
        pass

def use_record_qid(**kwargs):
    _record = CheckBookRatio(**kwargs)
    _record.insert_record_qid()


class NewCheckBook(object):
    def __init__(self, **kwargs):
        pass

    def mongo_insert(self):
        pass

def use_recode_api(**kwargs):
    try:
        logger.info("[插入查定比记录][mongo][{0}]".format(int(time.time() * 1000)))
        recode_api = NewCheckBook(**kwargs)
        if recode_api.init_code == 0:
            recode_api.mongo_insert()
    except Exception, e:
        logger.info("[插入查定比记录失败][mongo][{0}]".format(str(e)))


class ApiCheckBook(object):
    def __init__(self, **kwargs):
        """
        source: string 爬虫请求源 没有时""
        t: string 实际api请求时间 时间戳 格式为"2018-04-10T17:04:44+08:00"
        radio_check: int 插定比类型 类型映射:1为search, 2为realtime, 3为create_order, 4为cancel_order, 5为pay, 6为cancel_confirm, 7为order_detail
        type: string api_name第三方接口标识
        error_id: int类型 返回业务层判断错误码
        msg: string类型 对方返回业务原文和状态码
        http_code: int类型 返回请求层http code
        req: string 请求原文 json格式字符串
        content: string 爬虫任务content
        resp: string 只在支付阶段记录API返回报文
        qid: string 爬虫qid 没有时""
        ptid: string 任务所发企业ID
        task_info: string 爬虫任务信息 没有时""
        key: string 收集日志关键字 "MJ_MD_SP_API_LOG"
        is_success: 是否请求成功(这里的成功是指对方是否正常返回数据，只有请求数据错误的时候才返回1) int类型 0代表正常返回 1代表请求有误
        :param kwargs:
        """
        try:
            self.t = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
            self.radio_check = kwargs.get('record_tuple', 1)
            self.type = kwargs.get('api_name', '')
            self.error_id = kwargs.get('error_id', '')
            self.task = kwargs.get("task")
            self.unionkey = kwargs.get("unionkey")
            self.source = de_module[self.unionkey]
            self.api_info = kwargs.get('api_info')
            self.msg = kwargs.get('msg', '')
            self.http_code = kwargs.get('httpcode', '')
            self.req = self.api_info
            try:
                self.content = self.task.content
            except:
                self.content = ''
            self.resp = kwargs.get('resp', '')
            if hasattr(self.task, 'req_qid'):
                self.qid = getattr(self.task, 'req_qid')
            else:
                self.qid = self.t
            self.qid = self.qid
            try:
                self.ptid = json.loads(self.task.ticket_info['auth'])['acc_mj_uid']
            except:
                self.ptid = 'error_001'
            try:
                self.task_info = self.task.ticket_info
            except:
                self.task_info = ''
            self.key = 'MJ_MD_SP_API_LOG'
            self.is_success = kwargs.get('is_success', '')
            self.init_code = 0
        except Exception as e:
            self.init_code = 1
            logger.info("[初始化查订比数据失败][mongo][{0}]".format(str(e)))

    def mongo_insert(self):
        """
        暂未打印日志 提供给运维收取
        插定比只做 mongo入库统计
        :return:
        """
        try:
            client = MongoClient("mongodb://root:miojiqiangmima@10.19.56.168:27017")
            db = client['new_api_spider_check']
            collection_api = db[self.source]
            insert_data = {
                'source': self.source,
                't': self.t,
                'radio_check': self.radio_check,
                'type': self.type,
                'error_id': int(self.error_id),
                'msg': str(self.msg),
                'http_code': self.http_code,
                'req': self.req,
                'content': self.content,
                'resp': str(self.resp),
                'qid': self.qid,
                'ptid': self.ptid,
                'task_info': self.task_info,
                'key': self.key,
                'is_success': self.is_success
            }
            collection_api.insert_one(insert_data)
            logger.info("[插入查定比记录成功][mongo][{0}]".format(self.qid))
            logger.info("\n" + self.logger_info)
            # logger.debug('\n' + NewCheckBook.logger_info)
        except Exception as e:
            logger.info("[插入查定比记录失败][mongo][{0}]".format(str(e)))
        finally:
            try:
                client.close()
            except Exception as mme:
                logger.info("[插入查定比mongo连接错误][mongo][{0}]".format(str(mme)))

    @property
    def logger_info(self):
        """
        可能有日志输出需求，留用
        :return:
        """
        data = {'source': self.source, 't': self.t, 'radio_check': int(self.radio_check),
                'type': self.type, 'error_id': int(self.error_id), 'msg': str(self.msg),
                'http_code': int(self.http_code),'req': json.dumps(self.req),
                'content': self.content, 'resp': self.resp, 'qid': self.qid,
                'ptid': self.ptid,'task_info': json.dumps(self.task_info),
                'key': self.key,'is_success':self.is_success}
        return json.dumps(data).replace("\n", "$$n")


def use_record_api(**kwargs):
    try:
        logger.info("[插入查定比记录][mongo][{0}]".format(int(time.time() * 1000)))
        recode_api = ApiCheckBook(**kwargs)
        if recode_api.init_code == 0:
            recode_api.mongo_insert()
    except Exception, e:
        logger.info("[插入查定比记录失败][mongo][{0}]".format(str(e)))

# 1为search, 2为realtime, 3为create_order, 4为cancel_order, 5为pay, 6为cancel_confirm, 7为order_detail
ratio_check_temp = {
    'real_time_price': 2,
    'create_order': 3,
    'cancel_order': 4,
    'pay': 5,
    'cancel_confirm': 6,
    'order_detail': 7,
}

# api状态码
api_code_list = [12,13,21,24]

# 这里需要每个人传入自己源的unionkey,api_name
# def check_log(*kwargs):
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kw):
#             result = func(*args, **kw)
#             which_api = func.__name__
#             radio_check = ratio_check_temp.get(which_api)
#             unionkey = kwargs[0]
#             try:
#                 api_name = kwargs[1]
#             except:
#                 api_name = ''
#             resp = ''
#             is_success = 0
#             error_id = result[0]
#             if error_id not in [0,1]:
#                 resp = result[1]
#                 if error_id not in api_code_list:
#                     is_success = 1
#             use_record_api(task='',
#                    unionkey=unionkey,
#                    api_name=api_name,
#                    record_tuple=radio_check,
#                    error_id=error_id,
#                    api_info={},
#                    msg='I am msg',
#                    httpcode=200,
#                    resp=resp,
#                    is_success=is_success)
#             return result
#         return wrapper
#     return decorator


if __name__ == "__main__":
    class Task():
        def __init__(self):
            self.req_qid = 123
            self.content = 'NULL&37806&1&20181222'
            self.ticket_info = {'room_info': [{"adult_info": [24,24], "child_info": []}],'auth': 'www.baidu.com'}

    task = Task()
    # 按照这种方式写
    use_record_api(task=task, # 任务
                   unionkey='jacApi', # 源名称
                   api_name='SearchRequest', # 接口名称
                   record_tuple=1, # 1为search, 2为realtime, 3为create_order, 4为cancel_order, 5为pay, 6为cancel_confirm, 7为order_detail
                   error_id=29, # 错误码
                   api_info={}, # api信息 可以不写
                   msg='I am msg', # 对方返回业务原文 错误时记录
                   httpcode=200, # 状态码
                   resp='I am resp',
                   is_success=0) # 新加的字段，是否请求成功，成功给0,错误给1(例如，当无房时，这里给的也是0)


    # @check_log('nuiTeeApi','book')
    # def order_detail(requery):
    #     return 22,'我是reason'

    # order_detail('requery')