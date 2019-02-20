#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy
from logger import logger
import requests, httplib, time
from selenium import webdriver
from func_log import func_time_logger
from user_agent_list import random_useragent, new_header
from utils import current_log_tag
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import traceback
from spider_queue_qps import queue_and_qps
import gevent
from ESlogger import HttpLogger
import parser_except
from frequency_limit import default_limiter
from requests.exceptions import SSLError

# executable_path='/home/spider/chromedriver'


js1 = '''{Object.defineProperties(navigator,{
             webdriver:{
               get: () => false
             }
           })}'''

js2 = '''{
        alert (
            window.navigator.webdriver
        )
    }'''

js3 = ''' {
        window.navigator.chrome = {
    runtime: {},
    // etc.
  };
    }'''

js4 = '''{
Object.defineProperty(navigator, 'languages', {
      get: () => ["zh-CN", "zh"]
    });
        }'''

js5 = '''{
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5,6],
  });
        }'''


class resp_base():
    def __init__(self):
        self.content = ''
        self.status = 200
        self.text = ''

    def raise_for_status(self):
        return self.status


class SimulatorSpider():

    def __init__(self, referer='', headers={}, p='', md5='', qid='', out_ip='', **kw):

        self.proxy = p
        self.md5 = md5
        self.qid = qid
        self.task_id = kw.get("task_id", "")
        self.source = kw.get("source", "")
        self.headers = headers
        self.br = self.create_browser(proxy=p)
        self.resp = None
        self.real_ip = None
        self.out_ip = ""
        self.proxy_inf = ""
        self.req_count = 0
        self.resp_base = resp_base()
        self.queue_info = {}

    def set_proxy(self, proxy, chrome_opt):
        proxy_type = 'NULL'
        if proxy and proxy != "REALTIME":
            if proxy.startswith('10.'):
                proxy_type = 'socks'
                chrome_opt.add_argument('--proxy-server=socks5://{}'.format(proxy))
                try:
                    self.real_ip = proxy
                except Exception as e:
                    pass
            else:
                self.real_ip = proxy.split(':')[0]
                proxy_type = 'http'
                chrome_opt.add_argument('--proxy-server=http://{}'.format(proxy))

        logger.debug('[框架设置代理][代理类型: %s][代理 ip: %s ]' % (proxy_type, proxy))

    def create_browser(self, proxy='', args=None):
        chrome_opt = webdriver.ChromeOptions()
        chrome_opt.add_argument('--headless')
        chrome_opt.add_argument(
            'user-agent="{}"'.format(new_header()))
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_opt.add_experimental_option("prefs", prefs)
        self.set_proxy(proxy, chrome_opt)
        chrome_opt.add_argument('--disable-gpu')
        if isinstance(args, list):
            for argument in args:
                chrome_opt.add_argument(argument)
        browser = webdriver.Chrome(chrome_options=chrome_opt)
        browser.set_page_load_timeout(50)
        return browser

    def run_js(self):
        self.br.execute_script(js1)
        self.br.execute_script(js3)
        self.br.execute_script(js4)
        self.br.execute_script(js5)

    def wait_xpath(self, wait_xpath_list):
        for xpath, status in wait_xpath_list:
            if status:
                WebDriverWait(self.br, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
            else:
                WebDriverWait(self.br, 30).until_not(EC.presence_of_element_located((By.XPATH, xpath)))

    def request(self, url, cookie=None, wait_xpath_list=None, run_js=False,):
        # 请求方法
        self.br.get(url)
        if cookie:
            for key, value in cookie.items():
                self.br.add_cookie({"name": key, 'value': value})
            self.br.refresh()
        if wait_xpath_list:
            self.wait_xpath(wait_xpath_list)
        if run_js:
            self.run_js()
        self.resp_base.content = self.br.page_source
        self.resp_base.text = self.br.page_source
        self.resp_base.status = 200
        return self.resp_base

    def click(self, click_xpath_list, wait_xpath_list=None, run_js=False):
        for click_xpath in click_xpath_list:
            self.br.find_element_by_xpath(click_xpath).click()
            gevent.sleep(0.5)
        if wait_xpath_list:
            self.wait_xpath(wait_xpath_list)
        if run_js:
            self.run_js()
        self.resp_base.content = self.br.page_source
        self.resp_base.text = self.br.page_source
        self.resp_base.status = 200
        return self.resp_base

    @func_time_logger
    def req(self, url='', req_type='request', click_xpath_list=None, wait_xpath_list=None, cookie=None, run_js=False, **kw):
        httpLogger = HttpLogger()
        httpLogger = copy.deepcopy(httpLogger)
        httpLogger.qid = self.qid
        httpLogger.task_id = self.task_id
        httpLogger.req_type = req_type
        httpLogger.source = self.source
        httpLogger.task_id = self.task_id
        httpLogger.qid = self.qid
        if url:
            httpLogger.url = url
        if click_xpath_list:
            httpLogger.click_xpath_list = click_xpath_list

        httpLogger.proxy_out = str(self.out_ip)
        httpLogger.proxy = str(self.proxy)
        httpLogger.proxy_inf = str(self.proxy_inf)
        httpLogger.retry_count = self.req_count
        try:
            if url:
                logger.debug(current_log_tag() + 'browser req start {}'.format(url))
            if click_xpath_list:
                logger.debug(current_log_tag() + 'browser req click_xpath {}'.format(click_xpath_list))

            logger.debug(current_log_tag() + 'browser req session_cookie {}'.format(cookie))
        except:
            logger.debug(current_log_tag() + '请求前获取部分参数失败')
        try:
            if url:
                self.resp = local_resp = self.request(url, cookie=cookie, wait_xpath_list=wait_xpath_list, run_js=run_js)
                return local_resp
            if click_xpath_list:
                self.resp = local_resp = self.click(click_xpath_list, wait_xpath_list, run_js)
                return local_resp
            else:
                return ''
        except Exception as why:
            if self.br:
                self.close()
            httpLogger.exception = str(traceback.format_exc())
            logger.debug(current_log_tag() + 'browser req end {1} {0} proxy[{2}] error:{3}'.format(url,
            click_xpath_list, self.proxy, traceback.format_exc()))
            raise

    def close(self):
        if self.br:
            self.br.close()
            self.br.quit()
            self.br = None




if __name__ == '__main__':
    # spider = SimulatorSpider()
    # cookie = "IHotelSearch=RoomPerson=undefined&RegionNameAlpha=Bangkok%20and%20vicinity&RegionName=%E6%9B%BC%E8%B0%B7%E5%8F%8A%E5%91%A8%E8%BE%B9&RegionId=178236&OutDate=2019-01-22&InDate=2019-01-21; IHotelSearchData=%7B%22InDate%22%3A%222019-01-21%22%2C%22OutDate%22%3A%222019-01-22%22%2C%22RegionId%22%3A%22178236%22%2C%22RegionName%22%3A%22%E6%9B%BC%E8%B0%B7%E5%8F%8A%E5%91%A8%E8%BE%B9%22%2C%22RegionNameAlpha%22%3A%22Bangkok%20and%20vicinity%22%7D"
    # spider.create_browser()
    # print spider.request('http://2018.ip138.com/ic.asp',cookie={'1':'2'})
    # # spider.browser.quit()
    # # spider.browser.create_options().add_argument('--proxy-server=socks5://10.10.233.246:48321')
    # print spider.request('http://2018.ip138.com/ic.asp',cookie={'1':'2'})
    # spider.close()
    pass
    # spider.request('http://ihotel.elong.com/region_178236/', cookie=cookie, xpath_list=[("//a[@class='page_next']",True)])
    # spider.click("//a[@class='page_next']", wait_xpath=[("//a[@class='pa1ge_next']", True),
    #                                                     ("//div[@class='progress-text']", False)])
    # spider.click("//a[@class='page_next']", wait_xpath=[("//a[@class='page_next']", True),
    #                                                     ("//div[@class='progress-text']", False)])
    # spider.click("//a[@class='page_next']", wait_xpath=[("//a[@class='page_next']", True),
    #                                                     ("//div[@class='progress-text']", False)])
    # spider.click("//a[@class='page_next']", wait_xpath=[("//a[@class='page_next']", True),
    #                                                     ("//div[@class='progress-text']", False)])
    a = resp_base()
    print(a.raise_for_status())