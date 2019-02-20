# -*- coding: UTF-8 -*-

import store_utils
import traceback
import functools
import types
import random
from copy import deepcopy
import requests
import zlib
from lxml import html as HTML
import json
import time
import abc
import gevent.event
import datetime
import urllib
import uuid
import parser_except

from pool import pool
from logger import logger
from greenlet import getcurrent
from collections import defaultdict
from collections import Iterable

from browser import MechanizeCrawler
from Simulato import SimulatorSpider
from pool_event_lock import block_async

from mioji.common.func_log import func_time_logger
from mioji.common.utils import get_md5, current_log_tag
from mioji.common.task_change import task_change_sass



# 不要代理
PROXY_NONE = 0
# 沿用上次的设置(遇到封禁 22、23框架会更换代理)
PROXY_FLLOW = 1
# 严格沿用上次的设置(遇到封禁 22、23框架会会重试但不会主动更换代理)
PROXY_FLLOW_HARD = 5
# 需要设置新代理
PROXY_REQ = 2
# 第一次
PROXY_REQ_FIRST = 3
# 永远不用代理，一般api
PROXY_NEVER = 4
PROXY_API = 6
PROXY_GOOGLE_MAPS = 7


slave_get_proxy = None

insert_db_dict = {}

class Spider(object):
    """
    """
    __metaclass__ = abc.ABCMeta
    # 源类型
    source_type = ''
    # 抓取目标， 例如 : {'hotel':{}, 'room':{'version':'InsertNewFlight'}}
    targets = {}
    # 与老爬虫关联， 例如 : {'pricelineFlight': {'required': ['Flight']}}
    old_spider_tag = {}
    # 不启用，默认启用
    unable = False
    # 排队
    queue_info = {}
    # 重试配置
    retry_info = {'max_try': 1, 'retry_codes': []}

    def __init__(self, task=None):
        assert self.source_type != '', '缺失正确的抓取类型'
        assert self.targets != {}, '缺失正确的抓取 parser'
        assert len(self.targets) > 0, parser_except.ParserException(1, '必须指明解析目标')
        self.task = task
        self.task_id = ""
        self.spider_taskinfo = {}
        self.is_verify = False
        self.need_proxy = True
        self.use_selenium = False
        self.browser = None
        self.__cpu_time = 0
        self.debug = True
        self.extra = {}
        self.user_datas = dict()
        self.verify_data = {'data': []}
        self._asy_temp_result = defaultdict(list)
        self.task_post_process_queue = None
        self.code = -1
        self.cost_crawl_time = None

        self._result = defaultdict(list)
        self.__targets_parser_func_dict = {}
        self.targets_required = self.targets
        self._crawl_targets_required = self.targets_required
        self.debug_info = {'pages': []}
        self.process_callback = None
        # 用于减少一次异步回调
        self.spider_frame_status = 0
        self.exception = None

        self.machine_type = None
        self.local_ip = None
        self.env = None

        for t in self.targets.keys():
            func_name = 'parse_' + t
            parse_func = getattr(self, func_name)
            self.__targets_parser_func_dict[t] = parse_func

    @func_time_logger
    def crawl(self):
        """
        """
        if hasattr(self.task, 'new_task_id'):
            cur_id = self.task.new_task_id
        else:
            cur_id = str(uuid.uuid1())
        self.spider_taskinfo = {'task_id': cur_id}
        getcurrent().spider_taskinfo = self.spider_taskinfo
        # 打印任务信息
        for k, v in self.task.__dict__.items():
            self.spider_taskinfo[k] = v
            try:
                logger.info(current_log_tag() + '[任务信息][%s][%s]' % (k, json.dumps(v)))
            except Exception:
                continue
        
        chains = self.targets_request()
        try:
            self.code = self.__crawl_by_chain(chains)
        except parser_except.ParserException as e:
            logger.exception(e)
            self.code = e.code
            self.exception = e.msg
            if e.retry_from_first:
                raise e
        return self.code


    @abc.abstractmethod
    def targets_request(self):
        """
        目标请求链：酒店列表、酒店详情、酒店评论等
        """

    def response_error(self, req, resp, error):
        """ 
        请求异常
        :param resp requests response
        :param error 异常
        """
    
        pass

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, task):
        if self.source_type.endswith('Hotel') and task and "List" not in self.source_type:
            task = task_change_sass(task)
        self._task = task

    @func_time_logger
    def __crawl_by_chain(self, chains):
        """ 
        从请求链中辨别请求类型，分别丢入不同的请求方法
        单一请求，并行请求，串行请求
        """
        code = 0
        try:
            for reqParse in chains:
                gevent.sleep(0)
                browser = self.__create_browser(reqParse.new_session)
                reqParse.spider = self
                t_req = reqParse.request()

                if isinstance(t_req, types.DictType): # 单一请求
                    new_result = self.__single_crawl(reqParse, browser, t_req, 0)

                elif isinstance(t_req, types.ListType):
                    # 爬虫有可能返回一个空列表！！！
                    if t_req:
                        if reqParse.async: # 并行抓取
                            list_result = self.__async_crawl_list(reqParse, browser, t_req)
                        else: # 串行请求
                            list_result = self.__crawl_list(reqParse, browser, t_req)
                        new_result, code = self.check_list_result(list_result, code) # $$$ 可以优化

                elif isinstance(t_req, types.GeneratorType): # 针对使用的yelid 调用方法的请求
                    list_result = self.__crawl_list(reqParse, browser, t_req)
                    new_result, code = self.check_list_result(list_result, code)
                
                self.__spider_append_result(new_result)

            if self.use_selenium and browser.br: 
                browser.close()
        except parser_except.ParserException as e:
            if self.use_selenium and browser.br:
                browser.close()
            logger.error(e)
            raise e
        except Exception:
            if self.use_selenium and browser.br:
                browser.close()
            logger.exception(
                current_log_tag() + '[新框架 持续请求 未知问题][ {0} ]'.format(traceback.format_exc().replace('\n', '\t')))
            raise parser_except.ParserException(parser_except.UNKNOWN_ERROR, 'e:{0}'.format(traceback.format_exc()))

        return code
        

    def __async_crawl_list(self, reqParse, browser, req_list):
        """
        并行抓取分页
        丢到协程池里
        """

        a_result = defaultdict(list)
        all_except = True
        all_ok = True
        one_exception = None

        params = []
        total_count = 0
        for req in req_list:
            total_count += 1
            params.append((reqParse, browser, req, total_count))

        result = block_async(pool, self.__single_crawl, params)

        success_count = 0
        error_req = []
        for a_res in result:
            err_or_data, is_data = a_res
            if is_data:
                success_count += 1
                all_except = False
                self.__target_append_result(a_result, err_or_data)
            else:
                all_ok = False
                args, kwargs, one_exception = err_or_data
                if hasattr(one_exception, 'retry_from_first') and one_exception.retry_from_first:
                    raise one_exception
                error_req.append((args[2], one_exception.message))
        if reqParse.binding:
            self.success_count = success_count
            self.all_count = total_count
        logger.debug(current_log_tag() + '[翻页抓取][并行抓取][ 成功 {0} / {1} ]'.format(success_count, total_count))
        if error_req:
            logger.debug(current_log_tag() + '[翻页抓取][并行抓取][ 失败页请求 {0} ]'.format(str(error_req)))
        return a_result, all_except, all_ok, one_exception


    def __crawl_list(self, reqParse, browser, req_list):
        """
        串行抓取分页
        """
        result = defaultdict(list)
        all_except = True
        all_ok = True
        one_exception = None

        total_count = 0
        success_count = 0
        error_req = []
        for req in req_list:
            gevent.sleep(0)
            # 串行增加翻页限制取消
            # if NEED_FLIP_LIMIT:
            #     if total_count >= MAX_FLIP:
            #         break
            total_count += 1
            try:
                success_count += 1
                res = self.__single_crawl(reqParse, browser, req, page_count=total_count)
                self.__target_append_result(result, res)
                all_except = False
            except Exception, e:
                all_ok = False
                one_exception = e
                error_req.append((req, one_exception.message))
                logger.exception(
                    current_log_tag() + '[新框架][页面解析异常][ {0} ]'.format(traceback.format_exc().replace('\n', '\t')))

                #  抛出生成器部分的异常
                if isinstance(req, types.GeneratorType):
                    raise e
        if reqParse.binding:
            self.success_count = success_count
            self.all_count = total_count
        logger.debug(current_log_tag() + '[翻页抓取][串行抓取][ 成功 {0} / {1} ]'.format(success_count, total_count))
        if error_req:
            logger.debug(current_log_tag() + '[翻页抓取][串行抓取][ 失败页请求 {0} ]'.format(str(error_req)))
        return result, all_except, all_ok, one_exception

    def prepare_request(self, request_template):
        """
        在抓取过程中由用户指定 req，用户在函数中直接修改
        :param request_template: 本次请求的 request_template
        """
        pass
        
    def __create_browser(self, create_new=False):
        """
        创建brwser对象
        """
        if not self.browser or create_new:
            if self.browser:
                self.browser.close()
            # 暂时通过机器类型判断
            if self.machine_type == "webdrive":
                browser = SimulatorSpider()
            else:
                browser = MechanizeCrawler()
            self.browser = browser
            return self.browser
        return self.browser

    def __spider_append_result(self, new_result):
        """
        向 self.result 中添加解析结果
        :param new_result: 必须为解析结果
        :return: None
        :调用回调方法
        """

        for k, v in new_result.items():
            if not v:
                continue
            data_bind = self.targets[k].get('bind', None)
            if data_bind:
                logger.debug("current_log_tag() + [ 抓取绑定 {0} ][ 数据绑定 {1} ]".format(k, data_bind))
                self._result[data_bind] += v
                logger.debug(current_log_tag() + "%s, length=%s, all=%s", k, len(v), len(self._result.get(k, [])))
            else:
                self._result[k] += v
                logger.debug(current_log_tag() + "%s, length=%s, all=%s", k, len(v), len(self._result.get(k, [])))
    
    def __single_crawl(self, reqParse, browser, request_template, page_count):
        """ 用于请求的基本方法
        """
        # 请求链中的header 可以被沿用
        headers = request_template['req'].get('headers', None)
        use_headers = request_template['req'].get('use_headers', False)
        if headers:
            browser.add_header(headers, use_headers)

        # 设置 res 的 默认值
        res = defaultdict(list)

        # 初始化请求参数

        local_req_count = 0
        reqParse.req_count = 0
        reqParse.is_forbidden = False
        reqParse.req_exception = None
        reqParse.proxy = None
        reqParse.content_length = 0

        self.__cpu_time += time.time() * 1000 

        while local_req_count < reqParse.retry_count:
            # 增加一次重试次数
            local_req_count += 1
            logger.debug(current_log_tag() + '[开始抓取][ {0} ]'.format(request_template['req'].get('url','')))
            # 外部传入请求次数，用于在 parse 过程中抛出的代理异常进行重新抓取
            try:
                resp = reqParse.crawl_data(request_template, browser, self.task.source)
            except parser_except.ParserException as e:
                traceback.print_exc()
                if reqParse.user_exc:
                    # 抛出用户在函数中抛出的错误
                    raise e
                # 错误码21/22/23 或 开发指定需要重试
                if e.code in (parser_except.PROXY_FORBIDDEN, parser_except.PROXY_INVALID, parser_except.REQ_ERROR, parser_except.PROXY_SSL) or e.need_retry:
                    reqParse.is_forbidden = True
                    if local_req_count >= reqParse.retry_count or e.retry_from_first:
                        raise e
                    else:
                        logger.debug(current_log_tag() + traceback.format_exc())
                        logger.debug(current_log_tag() + '[准备重试][错误由框架抛出][错误码：{0}][count:{1}]'.format(e.code, reqParse.req_count))
                        continue
                else:
                    raise e
            except Exception, e:
                if reqParse.user_exc:
                    # 抛出用户在函数中抛出的错误
                    raise e
                if local_req_count >= reqParse.retry_count:
                    raise e
                else:
                    continue  

            # 请求中增加 resp 的值
            request_template['resp'] = resp
            # 打印存储抓取结果
            self.response_callback(request_template, resp)          
            if reqParse.res_text == 'text':
                    res = resp.text
            else:
                res = resp.content
            try:
                logger.debug(
                    current_log_tag() + '[抓取结果][ {2} ][ {0} ... ... {1} ]'.format(res[:100], res[-100:],
                                                                                    request_template['req'][
                                                                                        'url']).replace('\n',
                                                                                                        '').replace(
                        '\t', ''))
            except Exception:
                pass
            # 如果本地运行，将不执行上传操作
            # import pdb; pdb.set_trace()
            if not self.debug and self.env!="local" :
                md5_key = get_md5(res)
                verify_task_info = {
                    'func_name': reqParse.request_func.__name__,
                    'page_index': page_count,
                    'retry_count': local_req_count - 1,
                    'md5_key': md5_key
                }
                # 把上传抓取页面至ucloud
                self.task_post_process_queue.put((res, self.task, md5_key))
                self.verify_data['data'].append(verify_task_info)

            point_time = time.time() * 1000
            try:
                convert_data = reqParse.convert(request_template, res)
            except Exception:
                if local_req_count >= reqParse.retry_count:
                    logger.debug(current_log_tag() + traceback.format_exc())
                    raise parser_except.ParserException(parser_except.DATA_FORMAT_ERROR,
                                                        '[traceback: {0}]'.format(traceback.format_exc()))
                else:
                    continue
            finally:
                self.__cpu_time += time.time() * 1000 - point_time

            # 数据解析部分
            point_time = time.time() * 1000
            try:
                res = reqParse.parse(request_template, self.__targets_parser_func_dict, convert_data, page_count,
                                     self._crawl_targets_required)

                break
            except parser_except.ParserException as e:
                if e.code in (parser_except.PROXY_FORBIDDEN, parser_except.PROXY_INVALID):
                    reqParse.is_forbidden = True

                    if local_req_count >= reqParse.retry_count or e.retry_from_first:
                        raise e
                    else:
                        logger.debug(current_log_tag() + '[准备重试][错误由爬虫抛出][错误码：{0}]'.format(e.code))
                        convert_data = None
                        continue
                else:
                    raise e
            except Exception:
                raise parser_except.ParserException(parser_except.PARSE_ERROR,
                                                    '[traceback:{0}]'.format(traceback.format_exc()))
            finally:
                self.__cpu_time += time.time() * 1000 - point_time
                self.response_callback(request_template, resp)
        have_ticket = False
        for k, v in res.items():
            if not v:
                continue
            self._asy_temp_result[k] += v
            have_ticket = True
        # 有票 && slave调用的爬虫才会异步回调
        if have_ticket and self.process_callback and not self.debug and self.env!="local":
            self.process_callback(task=self.task, spider=self, result_type="RUNNING")

        return res
    
    @property
    @func_time_logger
    def result(self):
        try:
            for k, v in self._result.items():
                logger.debug(current_log_tag() + '[抓取结果][key: {0}][value_len: {1}]'.format(k, len(v)))
        except Exception:
            pass
        return self._result

    @staticmethod
    def __target_append_result(result, new_result):
        """
        向 result 中添加数据
        :param result: 被添加量
        :param new_result: 添加量
        :return: None
        : 此处用了字典的单例。
        """
        for k, v in new_result.items():
            if not v:
                continue
            logger.debug(current_log_tag() + "%s, length=%s, all=%s", k, len(v), len(result.get(k, [])))
            result[k] += v

    @property
    def crawl_targets_required(self):
        return self._crawl_targets_required
    
    def user_append_reslut(self, target, result_items):
        self._result[target] += result_items
        logger.debug(current_log_tag() + "%s, length=%s, all=%s", target, len(result_items), len(self._result.get(target, [])))


    def check_list_result(self, list_result, code):
        """

        $$$ 得优化 $$$
        检查每一个请求项返回的页面内容
        :param list_result: result, all_except, all_ok, one_exception 传入四项参数，返回的结果列表，是否全部为异常，是否全部正常
        :return:
        result like:{'hotelList_room':[(),()]}
        code: 0 全部正确；36 有翻页错误
        """
        
        result, all_except, all_ok, one_exception = list_result
        if all_ok and not all_except:
            if result:
                code_res = 0
            else:
                code_res = 0
        elif result and not all_except:
            code_res =36
        elif not all_except:
            code_res = 0
        else:
            code_res = 37
        if code == 0:
            code = code_res
        if code == 37 and code_res == 0:
            code = 36
        
        return result, code

    def response_callback(self, req, resp):
        """
        resp.url 判断是否是抓取页面或其他
        """
        pass


def simulator(retry_count=3, binding=None,
              new_session=False, ip_type="test", content_length=0, user_retry= False):
    """
    :param retry_count: 请求重试次数
    :param proxy_type: 代理类型
    :param async: 多个req是否需要同步
    :param binding: 绑定的解析函数，支持 None, str, bytes, callable, 以及可迭代的前几种类型
    :param user_retry: 用户重试，将重试部分教给用户操作。标记为 True 后，会增加 user_retry_err_or_resp handler 交由用户处理重试部分
    :param multi: 是否为同时进行多个解析。标记为 True 后，将会在爬取全部页面后返回所有页面值。在 parse 函数中返回的 req 和 data 分别为 list 。
    :param content_length: 是否需要判断 content_length 合法，None 不需要判断，0 或其他正整数，content_length 需要大于设置值
    :param new_session: 新的browser session
    :return: 返回 ReqParse 类型
    :ip_type: 决定使用国内代理(internal)还是国外(foreign)的
    """

    def call(func):
        req = SimParse(func, retry_count, binding, new_session, ip_type, content_length,user_retry)
        return req

    return call


def request(retry_count=3, proxy_type=PROXY_REQ, async=False, binding=None, user_retry_count=0,
            user_retry=False, multi=False, content_length=0, new_session=False, ip_type="test", ip_num=1, res_text='text'):
    """
    :param retry_count: 请求重试次数
    :param proxy_type: 代理类型
    :param async: 多个req是否需要同步
    :param binding: 绑定的解析函数，支持 None, str, bytes, callable, 以及可迭代的前几种类型
    :param user_retry: 用户重试，将重试部分教给用户操作。标记为 True 后，会增加 user_retry_err_or_resp handler 交由用户处理重试部分
    :param multi: 是否为同时进行多个解析。标记为 True 后，将会在爬取全部页面后返回所有页面值。在 parse 函数中返回的 req 和 data 分别为 list 。
    :param content_length: 是否需要判断 content_length 合法，None 不需要判断，0 或其他正整数，content_length 需要大于设置值
    :param new_session: 新的browser session
    :return: 返回 ReqParse 类型
    :ip_type: 决定使用国内代理(internal)还是国外(foreign)的
    """

    def call(func):
        req = ReqParse(func, retry_count, proxy_type, async, binding, user_retry_count,
                       user_retry, multi, content_length, new_session, ip_type, ip_num, res_text)
        return req

    return call


class ReqParse(object):
    def __init__(self, func, retry_count=3, proxy_type=PROXY_REQ, async=False, binding=None, user_retry_count=0,
                 user_retry=False, multi=False, content_length=0, new_session=False, ip_type="test", ip_num=1, res_text='text'):
        self.__request_func = func
        if user_retry_count:
            self.retry_count = user_retry_count
        else:
            # 强制4次重试
            self.retry_count = 4
        # 解析格式
        self.res_text = res_text

        self.proxy_type = proxy_type
        self.async = async
        self.binding = binding
        self.req_count = 0

        self.request_template = None
        self.__result = None
        self.spider = None
        self.user_retry = user_retry
        self.user_exc = False
        self.need_content_length = content_length

        # 是否返回此种类型所有页面
        self.multi = multi

        # 初始化抓取标志
        self.is_forbidden = False
        self.req_exception = None
        self.proxy = None
        self.content_length = 0

        # 代理ip所需类型，国内or国外
        self.ip_type = ip_type

        # 代理ip请求数量
        self.ip_num = ip_num

        # session browser
        self.new_session = new_session

    @property
    def request_func(self):
        return self.__request_func

    def request(self):
        return self.__request_func()

    

    def __crawl_data_str(self, request_template, browser):
        resp = None
        try:
            # 使用方法修改，用户直接修改 request_template 中的值
            self.spider.prepare_request(request_template)

            # 获得 request_template 中的 req
            req = request_template['req']

            # browser.queue_info = self.spider.queue_info
            if hasattr(self.spider.task, 'req_qid'):
                browser.qid = self.spider.task.req_qid
            else:
                browser.qid = ""
            browser.task_id = self.spider.task.task_id
            browser.source = self.spider.task.source
            browser.tid = self.spider.task.tid
            browser.ori_type = self.spider.task.ori_type

            resp = browser.req(**req)
            # 网络错误，异常抛出
            resp.raise_for_status()
            content_length = len(resp.content)
            if isinstance(self.need_content_length, int):
                logger.debug(
                    current_log_tag() + '[爬虫 content_length={1} 检测][页面长度需要大于 {0}]'.format(self.need_content_length,
                                                                                          content_length))
                if content_length <= self.need_content_length:
                    raise parser_except.ParserException(parser_except.PROXY_INVALID, msg='data is empty')
            elif self.need_content_length is None:
                logger.debug(current_log_tag() + '[爬虫无需 content_length 检测]')
            else:
                logger.debug(
                    current_log_tag() + '[未知 content_length 检测类型][type: {0}]'.format(
                        str(type(self.need_content_length))))
            return resp, content_length
        # timeout
        except requests.exceptions.SSLError as e:
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_SSL, msg=str(e), error=e)
        except requests.exceptions.ProxyError as e:  # 代理失效
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg='Proxy Error', error=e)

        except requests.exceptions.ConnectTimeout as e:
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, msg='Request connect Timeout', error=e)
        except requests.exceptions.ReadTimeout as e:
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, msg='Request read Timeout', error=e)
        except requests.exceptions.Timeout as e:
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, msg='Request Timeout', error=e)

        except requests.exceptions.ConnectionError as err:
            self.spider.response_error(request_template, resp, err)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=str(err))

        except requests.exceptions.HTTPError as err:  # 4xx 5xx 的错误码会catch到
            self.spider.response_error(request_template, resp, err)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=str(err), error=err)

        except requests.exceptions.RequestException as err:  # 这个是总的error
            self.spider.response_error(request_template, resp, err)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=str(err), error=err)
        except Exception as e:  # 这个是最终的error
            self.spider.response_error(request_template, resp, e)
            raise parser_except.ParserException(parser_except.PROXY_INVALID, msg=traceback.format_exc())

    def crawl_data(self, request_template, browser, source_name):
        """
        页面抓取函数
        :param request_template: 请求字典
        :param browser: 抓取浏览器
        :param source_name: 源名称
        :return: 返回抓取结果 response 对象
        """
        try:
            logger.debug(current_log_tag() + 'crawl %s, retry_count: %s', self.__request_func.__name__, self.req_count)
            # 代理装配
            self.browser_set_proxy(browser, source_name)

            resp, self.content_length = self.__crawl_data_str(request_template, browser)

            # todo 修改 user_retry 返回的结果
            if self.user_retry:
                try:
                    user_check = self.spider.user_retry_err_or_resp(resp, self.req_count, request_template, False)
                except Exception as e:
                    self.user_exc = True
                    raise e

                # 当用户返回 True 时
                if user_check:
                    return resp
                else:
                    raise parser_except.ParserException(parser_except.PROXY_INVALID,
                                                        '代理异常')
            else:
                return resp
        except parser_except.ParserException, e:
            self.is_forbidden = e.code in (
                parser_except.PROXY_FORBIDDEN, parser_except.PROXY_FORBIDDEN, parser_except.REQ_ERROR)
            self.req_exception = e
        except Exception, e:
            self.req_exception = parser_except.ParserException(parser_except.REQ_ERROR, 'req exception:{0}'.format(e))

            # 如果有用户异常，则置位用户重试
            if self.user_exc:
                if isinstance(e, parser_except.ParserException):
                    self.req_exception = e

        finally:
            if self.req_exception:
                code = self.req_exception.code
            else:
                code = 0

        if self.req_exception:
            raise self.req_exception

    @func_time_logger
    def convert(self, request_template, data):
        data_con = request_template.get('data', {})
        c_type = data_con.get('content_type', 'string')
        logger.debug(current_log_tag() + 'Converter got content_type: %s', c_type)
        if c_type is 'html':
            return HTML.fromstring(data)
        elif c_type is 'json':
            return json.loads(data)
        elif isinstance(c_type, types.MethodType):
            try:
                return c_type(request_template, data)
            except:
                raise parser_except.ParserException(-1, 'convert func muset error{0} ,func：{1}'.format(
                    traceback.format_exc(), c_type))
        else:
            return data
    
    def browser_set_proxy(self, browser, source_name):
         # 不使用代理、永远不使用代理
        if self.proxy_type == PROXY_NONE or self.proxy_type == PROXY_NEVER:
            browser.set_proxy(None)

        # 严格使用上次代理
        if self.proxy_type == PROXY_FLLOW_HARD:
            pass
        elif self.proxy_type == PROXY_API:
            browser.set_proxy({"PROXY_API": {'http': 'http://10.10.16.68:3128', 'https': 'https://10.10.16.68:3128'}})
        elif self.proxy_type == PROXY_GOOGLE_MAPS:
            google_maps_proxy = random.choice(["10.11.105.46:8888","10.11.37.111:8888"])
            browser.set_proxy({"PROXY_GOOGLE_MAPS": {"http": "http://"+google_maps_proxy,"https": "https://"+google_maps_proxy}})
        # 请求代理 或 "被封禁 且 不是永远不使用代理" 主动设置代理
        elif self.proxy_type == PROXY_REQ or self.is_forbidden:
            verify_info = self.spider.machine_type
            proxy_info = w_get_proxy(self.spider.debug, source=source_name, task=self.spider.task, verify_info=verify_info)
            browser.req_count = self.req_count

            if proxy_info != "REALTIME" and proxy_info:
                self.proxy = proxy_info
                self.spider.proxy = self.proxy
                out_ip = proxy_info[-1]
                browser.proxy_inf = out_ip
                if isinstance(out_ip, list):
                    out_ip = json.loads(out_ip[0])['resp'][0]['ips'][0]['external_ip']
                    browser.out_ip = out_ip
                else:
                    browser.out_ip = ""
                proxy = proxy_info[0]
            else:
                proxy = proxy_info
            browser.set_proxy(proxy)

    @func_time_logger
    def parse(self, request_template, targets_bind, converted_data, page_index, required=None, multi_last=False):
        result = defaultdict(list)
        parsed = set()
        if not multi_last:
            parser_list = request_template.get('user_handler', [])
            for parser in parser_list:
                if parser not in parsed:
                    logger.debug(current_log_tag() + 'user parser %s', parser)
                    parser(request_template, converted_data)

        # 通过 parse 更新 result 信息
        def parse_result(parser):
            # 判断是否为有解析需要，且在需解析目标中
            parser_name = parser.__name__.split('_', 1)[1]
            if parser_name in required:
                logger.debug(current_log_tag() + 'parse target %s', parser_name)
                
                per_result = parser(request_template, converted_data)
                if per_result is not None:
                    if per_result:
                        start = datetime.datetime.now()
                        if isinstance(per_result, types.ListType):
                            # 添加 guest_info
                            store_utils.add_index_info(
                                self.spider.targets.get(parser_name, {}).get('version', None),
                                per_result, page_index)
                            # 添加 stopby 信息
                            store_utils.add_stop_by_info(
                                self.spider.targets.get(parser_name, {}).get('version', None),
                                per_result, self.spider.task)
                            result[parser_name].extend(per_result)
                        elif isinstance(per_result, types.DictType):
                            result[parser_name].append(per_result)
                        logger.debug(
                            current_log_tag() + '[结果保存][不使用压缩][用时： {0} ]'.format(
                                datetime.datetime.now() - start))

        # 解析目标，酒店、房间、等
        # for target, parser in targets_bind.items():
        if isinstance(self.binding, Iterable) and not isinstance(self.binding, (str, bytes)):
            for binding in self.binding:
                # 对 binding 种类进行兼容判断
                if binding is None:
                    continue
                elif isinstance(binding, (str, bytes)):
                    parser = targets_bind.get(binding, '')
                    if parser == '':
                        TypeError('无法从 targets 中获取 parser {0}'.format(binding))
                elif callable(binding):
                    parser = binding
                else:
                    raise TypeError('不支持绑定类型 {0} 的 {1}'.format(type(binding), repr(binding)))
                # 更新 result 信息
                parse_result(parser)

        elif isinstance(self.binding, (str, bytes)):
            parser = targets_bind.get(self.binding, '')
            if parser == '':
                TypeError('无法从 targets 中获取 parser {0}'.format(self.binding))

            # 更新 result 信息
            parse_result(parser)

        elif callable(self.binding):
            parser = self.binding
            # 更新 result 信息
            parse_result(parser)

        return result

class SimParse(ReqParse):
    def browser_set_proxy(self, browser, source_name):
        pass
        

def mioji_data(object):
    pass
# other
def w_get_proxy(debug, source, task, verify_info):
    if debug and not slave_get_proxy:
        print 'debug，and not define get_proxy，so can’t get proxy '
        return None
    p = slave_get_proxy(source=source, task=task, verify_info=verify_info)
    if not p:
        raise parser_except.ParserException(parser_except.PROXY_NONE, 'get {0} proxy None'.format(source))
    return p