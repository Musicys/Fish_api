import json
import datetime
import string
import logging
from functools import partial

log = logging.getLogger()


def is_valid(s, func):
    try:
        func(s)
        return True
    except:
        return False


# 判断是否是数字
is_valid_num = partial(is_valid, func=float)

# 判断是否是整形
is_valid_int = partial(is_valid, func=int)

# 判断是否是float
is_valid_float = partial(is_valid, func=float)

# 判断是否能json.dumps
is_valid_json = partial(is_valid, func=json.dumps)

# 判断是否能json.loads
is_valid_loads = partial(is_valid, func=json.loads)


# 判断是否datetime
def is_date_type(v):
    return isinstance(v, (datetime.date, datetime.time))


# 判断只有字母数字
def just_letters_int_func(s):
    range_in = string.digits + string.ascii_letters
    for i in s:
        if i not in range_in:
            raise ValueError


just_letters_int = partial(is_valid, func=just_letters_int_func)


# 校验中文
def check_contain_chinese(check_str):
    for ch in check_str.decode('utf-8'):
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False
