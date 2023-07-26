"""适用于内部HTTP请求的客户端"""

import time
import json
import logging

from mtools.base.httpclient import RequestsClient

from mtools.utils.tools import parse_params
from mtools.resp.excepts import ParamError, HttpResultError

log = logging.getLogger()


class HTTPClient(RequestsClient):
    """相对于父类处理了返回结果"""

    allow_methods = ['post', 'get', 'post_json']

    def call(self, method, url, params):

        if method not in self.allow_methods:
            raise ParamError('请使用 {",".join(self.allow_methods)} 方法')
        method = getattr(super(), method, None)

        # 解析内容
        t1 = time.time()
        content = method(url, params)
        t2 = time.time()
        data = json.loads(content)
        t3 = time.time()
        log.info(f'http_time={t2-t1}|parse_params_time={t3-t2}')

        if not data:
            raise HttpResultError('没有返回或者无法解析')

        if not ('respcd' in data and 'data' in data and 'respmsg' in data):
            raise HttpResultError('返回数据无法解析')

        respcd = data['respcd']
        rdata = data['data']
        respmsg = data['respmsg']

        if respcd != '0000':
            raise HttpResultError(f'{respcd}:{respmsg}')

        return rdata

    def post(self, url, params):
        return self.call('post', url, params)

    def get(self, url, params):
        return self.call('get', url, params)

    def post_json(self, url, params):
        return self.call('post_json', url, params)
