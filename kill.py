#!/usr/bin/env python  
import os
import requests
import time 
import sys

# os.system(" ps -ef | grep 'bossStatus.py' | grep -v 'grep' | awk '{print $2}' | xargs kill -9 ")

os.system("pip install -r /home/SpiderFrame3/conf/requirements.txt")

os.system("ps -ef | grep 'slave' | grep -v 'grep' | awk '{print $2}' | xargs kill -9 ")