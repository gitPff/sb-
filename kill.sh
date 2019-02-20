#!/usr/bin/env python
# 暂停魔山
sh /usr/local/monitor_shell/monitor_control.sh -p 60

CURR_PATH=`cd $(dirname $0);pwd;`
echo $CURR_PATH
cd $CURR_PATH
source ./slave_process.sh
# 获取进程数
get_process_size ${slave_group}
proce_size=$?

python kill.py ${proce_size}

