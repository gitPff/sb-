#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年11月8日

@author: dujun
'''

TASK_ERROR = 12
NEW_QPS_OVERFLOW = 125
PROXY_NONE = 21
PROXY_INVALID = 22
PROXY_FORBIDDEN = 23
PROXY_SSL = 22001

REQ_ERROR = 2
DATA_FORMAT_ERROR = 3

PARSE_ERROR = 27
DATA_NONE = 24
UNKNOWN_ERROR = 25
EMPTY_TICKET = 29

# 明确无票
CLEAR_EMPTY_TICKET = 291

STORAGE_ERROR = 31
STORAGE_UNKNOWN_ERROR = 32
RABBITMQ_ERROR = 33
MYSQL_ERROR = 34
RABBITMQ_MYSQL_ERROR = 35

FLIP_WARRING = 36

API_ERROR = 89
API_NOT_ALLOWED = 90
API_EMPTY_DATA = 92
SLAVE_ERROR = 41

DEFAULT_MSG = {
    REQ_ERROR: "request error",
    TASK_ERROR: "task error",
    PROXY_NONE: "can not get proxy error",
    PROXY_INVALID: "网络错误",
    PROXY_FORBIDDEN: "task error",
}


class ParserException(Exception):
    TASK_ERROR = 12
    PROXY_NONE = 21
    NEW_QPS_OVERFLOW = 125
    PROXY_INVALID = 22
    PROXY_FORBIDDEN = 23
    PROXY_SSL = 22001
    REQ_ERROR = 2
    DATA_FORMAT_ERROR = 3

    PARSE_ERROR = 27
    DATA_NONE = 24
    UNKNOWN_ERROR = 25
    EMPTY_TICKET = 29
    # 明确无票
    CLEAR_EMPTY_TICKET = 291

    STORAGE_ERROR = 31
    STORAGE_UNKNOWN_ERROR = 32
    RABBITMQ_ERROR = 33
    MYSQL_ERROR = 34
    RABBITMQ_MYSQL_ERROR = 35

    FLIP_WARRING = 36

    API_ERROR = 89
    API_NOT_ALLOWED = 90
    API_EMPTY_DATA = 92

    MSG_F = 'code: {0}, msg:{1}, need retry:{2},retry_from_first:{3},retry_from_first_count:{4},error:{5}'

    def __init__(self, parser_error_code, msg='', error=None):
        self.code = parser_error_code
        self.msg = msg
        self.need_retry = False
        self.error = error
        self.retry_from_first = False
        self.retry_from_first_count = 3

    def __str__(self):
        return ParserException.MSG_F.format(self.code, self.msg, self.need_retry, self.retry_from_first, self.retry_from_first_count, self.error)

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    try:
        raise ParserException(22, 'error msg')
    except ParserException, e:
        import traceback

        print traceback.format_exc()
        print("parser error: {0}".format(e))
    except Exception, e:
        print str(e)
