'''Web Api Handler for DevOps Projects -- fanxin-group'''

import json
import config
import logging
from urllib import parse

from mtools.web.core import Handler
from mtools.web import session

from mtools.base.builder import builder_map

log = logging.getLogger()


__version__ = '1.0.0'


class BuildHandler(Handler):
    '''BuildHandler是处理请求的工具集合Handler

    1. 包含builder中的所有的工具，工具按照插件的概念
       使用时加载，并且为工具提供本次请求的数据和状态
    ArgsBuilder: 处理请求的的参数，用来验证数据类型和业务类型等
    ListBuilder: 用来处理分页请求数据
    ExpoBuilder: 用来处理导出到文件的处理

    '''

    def initial(self):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        origin = self.req.environ.get('HTTP_ORIGIN', '')
        self.set_headers({'Access-Control-Allow-Origin': origin})
        self.set_headers({'Access-Control-Allow-Credentials': 'true'})
        self.set_headers({'Access-Control-Allow-Headers': '*'})

        # 设置builder
        self._builder_map = builder_map

        # 加载本次请求的信息
        ses = {}
        method = self.req.method.lower()
        self._ses_fill = False

        self.source = {'args': {}, 'ses': ses, 'method': method}

    def __getattr__(self, name):
        '''加载builder工具'''

        if self._builder_map and name in self._builder_map:

            args = self._get_args()
            self.source['args'] = args

            if not self._ses_fill and getattr(self, 'ses', None):
                self._ses_fill = True
                self.source['ses'] = self.ses.data

            # 实例化builder
            builder_cls = self._builder_map[name]
            builder = builder_cls(self.source)
            setattr(self, builder.name, builder)
            return builder

        raise AttributeError

    def _get_args(self):
        '''获取本次请求的参数

        mtools中不解析list格式的json
        这里需要额外的处理
        同时需要处理敏感字段

        '''

        # default check
        validator = getattr(self, 'validator', None)
        if validator:
            args = validator.data
        else:
            args = self.req.inputjson()

        # 解析[]json数据
        if not args and self.req.data:
            if isinstance(self.req.data, bytes):
                self.req.data = self.req.data.decode('utf8')
            if self.req.data[0] == '[' and self.req.data[-1] == ']':
                try:
                    args = json.loads(self.req.data)
                except Exception:
                    log.warn('MH> load json data failed')
                    args = {}

        return args

    def class_name(self):
        return self.__class__.__name__

    def initial_session(self):
        token_value = self.get_cookie(
            config.SESSION.get('cookie_name', 'devplat_session_id'))
        if not token_value:
            d = self.req.inputjson()
            if '_token' in d:
                token_value = d['_token']
        ses = session.create(config.SESSION, token_value)
        self.ses = ses

    def run_builder(self, builder_cls, *arg, **kw):
        args = self._get_args()
        self.source['args'] = args
        self.source['client_ip'] = self.req.clientip()
        if not self._ses_fill and getattr(self, 'ses', None):
            self._ses_fill = True
            self.source['ses'] = self.ses.data
        builder = builder_cls(self.source)
        builder.init(*arg, **kw)
        return builder.run()

    def set_filename(self, filename, disposition=None):
        """设置返回文件名
        额外设置返回header.Uyu-Filename, 部分场景需要用到
        """
        disposition = disposition or 'attachment'
        filename_encode = filename.encode('utf-8').decode('ISO-8859-1')
        self.set_headers({'Content-Disposition': f'{disposition};filename="{filename_encode}"'})
        self.set_headers({'Uyu-Filename': parse.quote(filename)})
        self.set_headers({'MIME-Version': '1.0'})

    def expo_xlsx(self, filename, bin_data):
        self.set_filename(filename)
        return bin_data
