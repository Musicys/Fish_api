import json
import logging
import datetime

from mtools.resp.excepts import ParamError
from mtools.resp.define import DT_FMT, DTM_FMT, DTMF_FMT

log = logging.getLogger()


class Field(object):

    def __init__(self, must=False, default=None, name=''):
        # self.value = value
        self.must = must
        self.default = default
        self.name = name

    def __call__(self, f):
        def wrap(_self, value):
            self.value = value
            try:
                self.name = str(f.__name__)
            except:
                self.name = ''
            self.do()
            r = f(_self, self.value)
            return r
        return wrap

    def _type_fn(self, v):
        return v

    def _type_check(self):
        try:
            return self._type_fn(self.value)
        except Exception:
            raise ParamError(f'|{self.name} 参数类型错误')

    def _none_check(self):
        if self.value in ('', None):
            return True
        return False

    def do(self):
        is_none = self._none_check()
        # 校验必传
        if is_none:
            if self.must:
                raise ParamError(f'缺少必填参数{self.name}')
            elif self.default:
                self.value = self.default
                self.value = self._type_check()
            else:
                self.value = None
        else:
            self.value = self._type_check()


class Int(Field):

    _type_fn = int


class Float(Field):

    _type_fn = float


class Str(Field):

    _type_fn = str


class List(Field):

    def _type_fn(self, value):
        if not isinstance(value, (list, tuple)):
            raise ParamError('not list')
        return value



class Date(Field):

    def _type_fn(self, value):
        return datetime.datetime.strptime(value, DT_FMT)


class DateTime(Field):

    def _type_fn(self, value):
        return datetime.datetime.strptime(value, DTM_FMT)


class DateTime64(Field):

    def _type_fn(self, value):
        return datetime.datetime.strptime(value, DTMF_FMT)


class JsonStr(Field):

    _type_fn = json.loads
