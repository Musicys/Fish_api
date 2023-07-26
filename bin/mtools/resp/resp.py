import json
import math

from mtools.resp import define
from mtools.resp.define import OK
from mtools.resp.excepts import DevplatException


def error(respcd, respmsg='', data=None):
    return json.dumps({
        "respcd": respcd,
        "respmsg": respmsg or define.get_errmsg(respcd),
        "data": data or {}
    })


def success(data, respmsg=''):
    return json.dumps({"respcd": "0000", "respmsg": respmsg, "data": data})


def check_rpc_resp(resp):
    # code
    code_str = '%04d' % math.fabs(int(resp.retcode))
    if code_str == OK:
        return resp.result

    respcd, respmsg, data = code_str, '', None
    if isinstance(resp.result, str):
        respmsg = resp.result
    elif isinstance(resp.result, dict):
        respmsg = resp.result.get('respmsg')
        data = resp.result.get('data')
    else:
        data = resp.result

    raise DevplatException(respmsg=respmsg, respcd=respcd, data=data)
