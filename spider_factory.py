# -*- coding: UTF-8 -*-


import traceback
import importlib
import pkgutil
import os
from mioji.common.spider import Spider
import inspect
from mioji.common.logger import logger



class SpiderFactory(object):
    """
    :note:  抓取之前请设置 mioji.common.spider.insert_db 和 mioji.common.spider.get_proxy
    :see: get_spider
    :see: get_spider_by_targets
    :see: get_spider_by_old_source
    """

    def __init__(self):
        """
        Constructor
        """
        self.__spider_list = dict()


    def all(self):
        return self.__spider_list

    def load(self):
        logger.debug('=======初始化Spider======')
        spider_list = {}

        source_module_names = find_module_names('spider')
        for source in source_module_names:

            logger.debug("找到source：%s", source)
            spider_package = 'spider.' + source

            spider_module_names = find_module_names(spider_package)
            for spider_module in spider_module_names:
                try:
                    logger.info("找到module: %s", spider_module)
                    if spider_module.endswith('_spider'):
                        desc = init_spider(spider_package + '.' + spider_module)
                        if desc:
                            desc[0]['source_key'] = source
                            spider_list[desc[0]['source_type']] = desc[0]
                except Exception:
                    logger.info("寻找并加载 [ module ]: {0} 时出现异常，[ {1} ]".format(spider_module, traceback.format_exc()))

        self.__spider_list = spider_list
        print('spiders: ', self.__spider_list)
        logger.info('=======spider init complete======')


    def get_spider(self, source):
        spider = self.__spider_list.get(source, {})
        return spider.get('spider_class')




def find_module_names(name):
    p = importlib.import_module('.%s'%name,'mioji')
    c = pkgutil.iter_modules([os.path.dirname(p.__file__)])
    file_list = [name for _, name, _ in c]
    return file_list


def init_spider(module_name):
    """
    :param module_name: like  spider.booking.hotel_list_spider
    :return: 理论上只有一个spider
    """
    print(module_name)
    spider_module = importlib.import_module('.' + module_name, 'mioji')
    spider_list = []
    for attr in inspect.getmembers(spider_module):
        if inspect.isclass(attr[1]) and attr[1].__module__.endswith('_spider') and attr[1].__module__.endswith(module_name):
            if issubclass(attr[1].__bases__[0], Spider) :
                # 当为 Spider 子类或同类时加载
                try:
                    spider_clazz = getattr(spider_module, attr[0])
                    spider = spider_clazz()
                    if isinstance(spider, Spider):
                        spider_desc = {}
                        spider_desc['source_type'] = spider.source_type
                        spider_desc['spider_class'] = spider_clazz
                        spider_desc['targets'] = spider.targets.keys()
                        spider_list.append(spider_desc)
                except:
                    logger.exception('instance spider[%s]', attr[1])

    return spider_list





# if __name__ == '__main__':
#     from mioji.common.task_info import Task
#     import common.insert_db
#     from common.common import get_proxy
#     from mioji import spider_factory
#     from mioji.spider_factory import factory
#
#     insert_db = common.insert_db
#     get_proxy = get_proxy
#     debug = False
#     print
#     "spider——adapter  " * 20
#     spider_factory.config_spider(insert_db, get_proxy, debug, is_service_platform=True)
#
#     task = Task()
#     li = ['OKA&ASB&20170720', 'LXR&LBV&20170510', 'CHI&GUM&20170520', 'MMK&AKL&20170510']
#     # task.content = "KIX&XIY&20170910"
#     # task.source = 'pricelineFlight'
#     task.content = 'PAR&BJS&20180921'
#     task.source = 'expediaFlight'
#     task.ticket_info = {"env_name": "test"}
#
#
#     # task.req_qid = 111111
#
#     def entry_test(task):
#         spider = factory.get_spider_by_old_task(task)
#         if spider is None:
#             spider = factory.get_spider_by_old_source(task.source)
#             if spider is None:
#                 return None
#             spider.task = task
#         return spider
#
#
#     spider = entry_test(task)
#     print
#     spider.crawl(cache_config={'enable': False})
#     print
#     spider.result
#
