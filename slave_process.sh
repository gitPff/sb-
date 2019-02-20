#!/bin/bash

function get_cpu_count(){
    cpu_count=`cat /proc/cpuinfo| grep 'processor'| sort| uniq| wc -l`
    if [ ${cpu_count} == "0" ]
    then
        echo "can't get cpu count set default 1"
        cpu_count=1
    fi
    echo "cup count is ${cpu_count}"
    return ${cpu_count}
}

function get_process_size(){
    slave_group=$1
    echo "slave_group is ${slave_group}"
    get_cpu_count
    cpu_count=$?
    return ${cpu_count}
}