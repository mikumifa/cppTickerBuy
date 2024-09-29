# 欢迎补充错误码
import datetime

ERRNO_DICT = {
    False: '抢票失败'
}


def withTimeString(string):
    return f"{datetime.datetime.now()}: {string}"
