#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
-------------------------------------------------
  @Author  : JiangZhao 
  @File    : task_change.py
  @Date    : 19/1/22 上午10:53
  @Software: PyCharm
-------------------------------------------------
"""


def task_change_sass(tasks):
    room_info = tasks.ticket_info.get("room_info", [])
    if not room_info:
        return tasks
    room = room_info[0]
    if 'occ' not in room:
        return tasks
    occ = int(room["occ"])
    num = int(room["num"])
    adults = []
    new_room = []
    for i in range(occ):
        adults.append(25)
    for i in range(num):
        new_room.append({"adult_info": adults, "child_info": []})
    tasks.ticket_info["room_info"] = new_room
    return tasks


if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()

    task.ticket_info['room_info'] = [
        {"adult_info": [33, ],
         "child_info": [7, 2]},
        {"adult_info": [33, 22],
         "child_info": [2, 3]}
    ]
    print task_change_sass(task)
