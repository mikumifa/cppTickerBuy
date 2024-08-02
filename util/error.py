# 欢迎补充错误码
import datetime

ERRNO_DICT = {
}


def withTimeString(string):
    return f"{datetime.datetime.now()}: {string}"
