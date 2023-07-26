import re
import time
import sys
import json
import urllib
import logging
import demjson3
import traceback

log = logging.getLogger()


def to_list(x):
    if not isinstance(x, (list, tuple, set)):
        return [x]
    return x


def get_fn(module, fn_name):
    if isinstance(module, str):
        module = sys[module]

    return getattr(module, fn_name, None)


def get_value(d, *keys):
    data = d or {}
    for k in keys:
        if data:
            data = data.get(k)
        else:
            return None
    return data

decimal_re = re.compile(r"decimal\('(\d+(?:\.\d+)?)'\)")
decimal_re_p = re.compile(r"Decimal\('(\d+(?:\.\d+)?)'\)")
datetime_re = re.compile(r'datetime\.datetime\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2}),\s*(\d{1,2}),\s*(\d{1,2}),\s*(\d{1,2})(?:,\s*(\d{1,6}))?\)')


def json_clear_bytes(params):

    if params[0] == 'b':
        params = params[1:]

    while params[0] == params[-1]:
        params = params[1:-1]
    return params


def parse_params(params, to_dict=False):
    if not params:
        return {}

    if params[0] in ('{', '[') and params[-1] in (']', '}'):

        try:
            params = demjson3.decode(
                params.encode('raw_unicode_escape'),
                encoding='utf8'
            )
        except demjson3.JSONDecodeError as e:
            try:
                if 'True' in params:
                    params = params.replace('True', 'true')
                if 'False' in params:
                    params = params.replace('False', 'false')
                if 'None' in params:
                    params = params.replace('None', 'null')
                if 'decimal' in params:
                    params = decimal_re.sub(r'\1', params)
                if 'Decimal' in params:
                    params = decimal_re_p.sub(r'\1', params)
                if 'datetime' in params:
                    params = datetime_re.sub(r'"\1-\2-\3 \4:\5:\6.\7"', params)
                params = demjson3.decode(
                    params.encode('raw_unicode_escape'),
                    encoding='utf8'
                )
            except Exception:
                log.warn(params)
                log.warn(traceback.format_exc())
                return {}
        except Exception:
            log.warn(params)
            log.warn(traceback.format_exc())
            return {}
    elif '=' in params and '{' not in params and '}' not in params:
        try:
            params = urllib.parse.parse_qsl(params)
            params = dict(params)
        except Exception:
            log.warn(traceback.format_exc())
            return {}

    if isinstance(params, str) and to_dict:
        return {'data': params}

    return params


if __name__ == '__main__':
    # a = parse_params("{'userid': '\\u6570\\u636e\\u9519\\u8bef', 'token': '9702b7d8-79d7-40f4-a345-729b01336c45', 'src': None}")
    # a = parse_params("'userid': '3107970', 'token': '9702b7d8-79d7-40f4-a345-729b01336c45', 'src': 'XL'", to_dict=True)
    a = "b'{'train_info': {'total': 0, 'week_cnt': datetime.datetime(2023, 3, 21, 16, 5, 37), 'today_cnt': datetime.datetime(2023, 3, 21, 16, 5, 37, 594000), 'remain_times': Decimal('9'), 'kk': Decimal('9.22')}, 'lease_info': {}, 'g3f_info': {'have_g3f_device': False}}'"
    a = "token=7c21f536-6e6b-4ccc-a917-a6c83a2590d6"
    a =  '{"id":3827189,"userid":1119665,"channel_id":3011142,"store_id":3011302,"device_id":3004607,"presc_id":11978,"record_id":0,"item_type":2,"presc_content":"[{\\"presc\\":{\\"dots_level\\":3,\\"dots_value\\":[\\"40.2\\",\\"448\\"],\\"flicker_level\\":1,\\"flicker_value\\":{\\"hz\\":0.2,\\"t\\":0.4},\\"optotype_level\\":19,\\"optotype_value\\":\\"4.8\\",\\"corrected_va_n_optotype_level\\":21,\\"time\\":120},\\"name\\":\\"RedFlicker_d\\",\\"item_name\\":\\"\\\\u7ea2\\\\u5149\\\\u95ea\\\\u70c1\\\\u53cc\\\\u773c\\",\\"id\\":\\"361547\\",\\"item_id\\":110,\\"count\\":1,\\"ctime\\":\\"2023-05-26 10:24:10\\",\\"presc_id\\":11978}]","state":1,"step":0,"times":0,"check_items":"[]","lng":"117.1075","lat":"39.0867","generation":3,"show_inscribe":0,"inscribe":"\\u4f18\\u773c\\u79d1\\u6280","device_sku":"XL03","src":2,"ctime":"2023-05-26 10:39:30","utime":"2023-05-26 10:39:30","client_time":null,"total_cnt":954}'
    # print(a)
    # a = parse_params(a)
    # log.info(a)
    # print(a)
    # a = json_clear_bytes(a)
    # print(a)
    print(len(a))
    time1 = time.time()
    a = parse_params(a)
    time2 = time.time()
    print(a)
    print(time2 - time1)
    # print(a['g3f_info'])

