#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import socket
try:
    import ConfigParser
except:
    import configparser as ConfigParser

os.environ["CONFIG_FILE"] = "./conf/service.conf"
os.environ["CONFIG_FILE"] = "/Users/miojilx/Desktop/git/SpiderFrame3/conf/service.conf"
config_file_path = os.environ["CONFIG_FILE"]

class ConfigHelper:

    def __init__(self, file_path=config_file_path):
        self.config = ConfigParser.ConfigParser()
        self.config.read(file_path)
        self.local_ip = get_local_ip()
        self.thread_num = int(self.config.get("slave", "thread_num"))
        self.env = self.config.get("slave", "env") # 机器环境
        self.machine_type = self.config.get("slave", "machine_type") # 机器类型
        self.parser_async_pool_size = int(self.config.get("slave", "parser_async_pool_size"))
        self.process_queue_size = int(self.config.get("server_info", "process_queue_size"))
        self.co_pool_size = int(self.config.get("server_info", "co_pool_size"))
        self.task_queue_size = int(self.config.get("server_info", "task_queue_size"))
        self.real_time_spider = int(self.config.get("server_info", "real_time_spider"))
        self.connect_time_spider = int(self.config.get("server_info", "connect_time_spider"))

        self.heart_beat_redis_host = self.config.get("redis", "heart_beat_redis_host")
        self.heart_beat_redis_port = int(self.config.get("redis", "heart_beat_redis_port"))
        self.heart_beat_redis_pwd = self.config.get("redis", "heart_beat_redis_pwd")
        self.heart_beat_redis_db = int(self.config.get("redis", "heart_beat_redis_db"))
        self.heart_beat_interval = int(self.config.get("redis", "heart_beat_interval"))

        self.ucloud_public_key = self.config.get("ucloud","public_key")
        self.ucloud_private_key = self.config.get("ucloud","private_key")
        self.ucloud_bucket = self.config.get("ucloud","bucket")

        self.target_async_size = 16
        self.need_proxy = False
        self.need_post_process = False

        self.local_port = 8080

    def record_local_port(self, port):
        self.local_port = port
    
    def __str__(self):
        return json.dumps(self.__dict__)

    def get_proxy_host(self):
        """ 确定环境后，读取对应环境的代理
        """
        if self.env == "OnlineHotel":
            self.proxy_host = self.config.get("proxy", "routine_proxy_host") 
        else:
            self.proxy_host = self.config.get("proxy", "verify_proxy_host")



def get_local_ip():
    res = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        res = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    return res

g_config = ConfigHelper()