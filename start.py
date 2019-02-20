# -*- coding: utf-8 -*-

import os

cpu_num = os.popen("cat /proc/cpuinfo| grep 'processor'| sort| uniq| wc -l")
cpu_num = int(cpu_num.read())
if cpu_num == 0:
    print "获取不到cpu数量，cpu数默认置为1"
    cpu_num = 1

local_info = os.popen("mioji-host").read()
local_name = local_info.split()[1]
env =  local_name.split(".")[-1]
host_name = os.system("hostname")

# 验证机器
# 并且会用于取代理的type
port = 8089
if "newverify_hotel" in local_name:
    name = "routine"
elif "newverify" in local_name:
    name = "verify"
elif "selenium" in local_name:
    name = "selenium"
elif "api" in local_name:
    name = "api"
else:
    name = "real"

# env 用于心跳
if "newverify_hotel" in local_name:
    env = "OnlineHotel"
elif "online" in local_name:
    if "ucc" in local_name or "uce" in local_name:
        env = "OnlineC"
    else:
        env = "OnlineD"
elif "test" in local_name:
    env = "Test"

for i in range(cpu_num):
    port = i + 8089
    os.system("""{ nohup stdbuf -oL python slave.py {port} {env} {name} 2>&3 | nohup cronolog /search/spider_log/rotation/%Y%m%d/%Y%m%d%H/slave.log_{port}.%Y%m%d%H.{HOST}.std ;} 3>&1 | nohup cronolog /search/spider_log/rotation/%Y%m%d/%Y%m%d%H/slave.log_{port}.%Y%m%d%H.{HOST}.err &""".replace("{port}", str(port)).replace("{HOST}", str(host_name)).replace("{env}", env).replace("{name}", name))