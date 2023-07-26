#coding=utf8
'''builder需要的类'''

import json
import logging
import datetime
import traceback

#log = logging.getLogger('')

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'


def trans_cols_to(column=''):
    '''对表做搜索需要转化其他字段为表字段

    设定value一定存在，根据rest的值和colu的值
    是否存在一共有4种情况
    rest,colu,解释
    y,n - 将转化后的值添加到原有的筛选
    y,y - 如果有相同的值(set&)，则取值，否则[-1]不存在
    n,y - 不存在
    n,n - 不存在

    '''
    def _(func):
        def wrapper(self, value):
            if not column:
                return func(self, value)
            # 准备rest的值
            rest = func(self, value)
            if rest is None:
                return None
            if not rest:
                rest = []
            elif not isinstance(rest, list):
                rest = [rest]
            # 初始化values和准备colu的值
            if column not in self.process_data:
                self.process_data[column] = []
            elif not isinstance(self.process_data[column], list):
                self.process_data[column] = [self.process_data[column]]
            colu = self.process_data[column]
            # 判断
            if not rest:
                self.process_data[column] = [-1]
            else:
                if not colu:
                    colu.extend(rest)
                else:
                    ret = set(colu) & set(rest)
                    if ret:
                        self.process_data[column] = list(ret)
                    else:
                        self.process_data[column] = [-1]
            return rest
        return wrapper
    return _


class ArgsChecker(object):

    def in_build(self):
        pass

    def after_build(self):
        pass

    def escape_fuzzy(self, value):
        '''将查询里面部分不兼容字段处理'''

        for i in ['%', '_']:
            if i in value:
                value.replace(i, '\\'+i)
        return '%{}%'.format(value)

    def _default(self, value):
        '''字段默认处理方法'''
        return value


class BaseInspector(object):

    instances = {}
    _debug = False

    def __new__(cls, *args, **kwargs):
        if cls.__name__ not in cls.instances:
            instance = object.__new__(cls, *args, **kwargs)
            cls.instances[cls.__name__] = instance
        return cls.instances[cls.__name__]

    def __init__(self, is_debug=False):
        self._debug = is_debug

    def _default(self, value):
        return value

    def _is_valid(self, v, f):
        try:
            return f(v)
        except Exception:
            if self._debug:
                print(traceback.format_exc())
                #log.warn(traceback.format_exc())
            return False

class Inspector(BaseInspector):
    '''业务逻辑中使用'''

    def v_int(self, value):
        return self._is_valid(value, int)

    def v_str(self, value):
        if isinstance(value, bytes):
            value = value.decode('utf8').strip()
        return self._is_valid(value, str)

    def v_datetime(self, value):
        if isinstance(value, datetime.datetime):
            return value
        dtck = lambda s: datetime.datetime.strptime(s, DATETIME_FMT)
        return self._is_valid(value, dtck)

    def v_date(self, value):
        dtck = lambda s: datetime.datetime.strptime(s, DATE_FMT)
        return self._is_valid(value, dtck)

    def v_num(self, value):
        return self._is_valid(value, float)

    def v_json(self, value):
        return self._is_valid(value, json.loads)

    def v_list(self, value):
        return self._is_valid(value, list)


class ArgsInspector(BaseInspector):
    '''针对前端参数的检测

    表单的值都是字符串
    json允许的值：字符串、数值、true、false、object、array

    被认为是空则返回None
    不是指定类型返回False
    正常解析是解析后的值

    '''

    def _none_check(self, value):
        if value in ('', None):
            return None
        return value

    def _false_check(self, value, types):
        if value is True or value is False:
            return False
        if not isinstance(value, types):
            return False
        return True

    def v_int(self, value):
        if self._none_check(value) is None:
            return None
        if value is True or value is False:
            return False
        return self._is_valid(value, int)

    def v_float(self, value):
        if self._none_check(value) is None:
            return None
        if not self._false_check(value, (int, float, str)):
            return False
        return self._is_valid(value, float)

    def v_str(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode('utf8').strip()
        if not self._false_check(value, (int, str, float)):
            return False
        return self._is_valid(value, str)

    def v_date(self, value):
        if isinstance(value, datetime.date):
            return value
        if self._none_check(value) is None:
            return None
        dtck = lambda s: datetime.datetime.strptime(s, DATE_FMT)
        return self._is_valid(value, dtck)

    def v_datetime(self, value):
        if isinstance(value, datetime.datetime):
            return value
        if self._none_check(value) is None:
            return None
        dtck = lambda s: datetime.datetime.strptime(s, DATETIME_FMT)
        return self._is_valid(value, dtck)

    def v_json(self, value):
        if self._none_check(value) is None:
            return None
        return self._is_valid(value, json.loads)

    def v_manual(self, value):
        return self._default(value)

    def v_split(self, value, processer=None, sp=','):
        if self._none_check(value) is None:
            return None
        if isinstance(value, bytes):
            value = value.decode('utf8').strip()
        if not isinstance(value, str):
            return False
        value_list = value.split(sp)
        value_list = [i.strip() for i in value_list if i.strip()]
        if not value_list:
            #log.warn('MH> v_split: no rest after split and strip')
            return None
        if not processer:
            return value_list
        value_list = [i for i in map(processer, value_list) if i is not None]
        for i in value_list:
            if i is False:
                return False
        return value_list

    def v_split_int(self, value):
        return self.v_split(value, self.v_int)

    def v_split_str(self, value):
        return self.v_split(value, self.v_str)

    def v_list(self, value, processer=None):
        if self._none_check(value) is None:
            return None
        if not isinstance(value, list):
            return False
        if not processer:
            return value
        value = [i for i in map(processer, value) if i is not None]
        return value if False not in value else False

    def v_list_str(self, value):
        return self.v_list(value, self.v_str)

    def v_list_int(self, value):
        return self.v_list(value, self.v_int)

def test_valid_func(test='all'):
    '''测试

    需要覆盖到
    1、正常情况
    2、False
    3、None

    key: '', 0, None, [], True, False

    '''
    misptor = ArgsInspector()
    print('start test')
    print('v_{} test start'.format(test))
    try:
        if test == 'int' or test == 'all':
            # other
            assert misptor.v_int('')==None
            # string
            assert misptor.v_int('-1')==-1
            assert misptor.v_int('12')==12
            assert misptor.v_int('0')==0
            assert misptor.v_int('kk')==False
            # number
            assert misptor.v_int(0)==0
            assert misptor.v_int(1)==1
            assert misptor.v_int(1.12)==1
            assert misptor.v_int(-1)==-1
            # array
            assert misptor.v_int([])==False
            assert misptor.v_int([1,2])==False
            # bool
            assert misptor.v_int(False) is False
            assert misptor.v_int(True) is False
            # null
            assert misptor.v_int(None)==None
        if test == 'str' or test == 'all':
            # other
            assert misptor.v_str('')==''
            # string
            assert misptor.v_str('kk')=='kk'
            assert misptor.v_str(b'kk')=='kk'
            # number
            assert misptor.v_str(0)=='0'
            assert misptor.v_str(12)=='12'
            assert misptor.v_str(-12)=='-12'
            assert misptor.v_str(0.11)=='0.11'
            # array
            assert misptor.v_str([])==False
            assert misptor.v_str([1,2])==False
            # bool
            assert misptor.v_str(True)==False
            assert misptor.v_str(False)==False
            # null
            assert misptor.v_str(None)==None
        if test == 'date' or test == 'all':
            dt = datetime.datetime(2019,12,12)
            # other
            assert misptor.v_date('')==None
            # string
            assert misptor.v_date('2019-12-12')==dt
            assert misptor.v_date('2019-12-')==False
            assert misptor.v_date('2019-12-12 12:12:12')==False
            # number
            assert misptor.v_date(12)==False
            assert misptor.v_date(-12)==False
            assert misptor.v_date(0)==False
            # array
            assert misptor.v_date([])==False
            assert misptor.v_date([1,2])==False
            # bool
            assert misptor.v_date(True)==False
            assert misptor.v_date(False)==False
            # null
            assert misptor.v_date(None)==None
        if test == 'datetime' or test == 'all':
            ddt = datetime.datetime(2019,12,12,12,12,12)
            # other
            assert misptor.v_datetime('')==None
            # string
            assert misptor.v_datetime('2019-12-12 12:12:12')==ddt
            assert misptor.v_datetime('2019-12-12 12:12:12  ')==False
            assert misptor.v_datetime('2019-12-12 12:12')==False
            # number
            assert misptor.v_datetime(-1.12)==False
            assert misptor.v_datetime(-1)==False
            assert misptor.v_datetime(0)==False
            assert misptor.v_datetime(1)==False
            assert misptor.v_datetime(211223)==False
            # array
            assert misptor.v_datetime([])==False
            # bool
            assert misptor.v_datetime(True)==False
            assert misptor.v_datetime(False)==False
            # null
            assert misptor.v_datetime(None)==None
        if test == 'float' or test == 'all':
            # other
            assert misptor.v_float('')==None
            # string
            assert misptor.v_float('-1')==-1.0
            assert misptor.v_float('-1.2134')==-1.2134
            assert misptor.v_float('0')==0.0
            assert misptor.v_float('12.34')==12.34
            assert misptor.v_float('0.0034')==0.0034
            assert misptor.v_float('0.0034d')==False
            # number
            assert misptor.v_float(-1)==-1.0
            assert misptor.v_float(0)==0.0
            assert misptor.v_float(0.0)==0.0
            assert misptor.v_float(1)==1.0
            assert misptor.v_float(123)==123.0
            # array
            assert misptor.v_float([])==False
            # bool
            assert misptor.v_float(False)==False
            assert misptor.v_float(True)==False
            # null
            assert misptor.v_float(None)==None
        if test == 'json' or test == 'all':
            # other
            assert misptor.v_json('')==None
            # string
            assert misptor.v_json('{"k":"2"}')=={'k': '2'}
            assert misptor.v_json('{}')=={}
            assert misptor.v_json('dfd')==False
            # number
            assert misptor.v_json(-1)==False
            assert misptor.v_json(0)==False
            assert misptor.v_json(1)==False
            # array
            assert misptor.v_json([])==False
            # bool
            assert misptor.v_json(False)==False
            assert misptor.v_json(True)==False
            # null
            assert misptor.v_json(None)==None
        if test == 'split' or test == 'all':
            # other
            assert misptor.v_split('')==None
            # string
            assert misptor.v_split(',,,')==None
            assert misptor.v_split('{"k":"2"}')==['{"k":"2"}']
            assert misptor.v_split('kkk,kkk')==['kkk', 'kkk']
            assert misptor.v_split('kkk.kkk', sp='.')==['kkk', 'kkk']
            assert misptor.v_split('kkk.kkk', sp=',')==['kkk.kkk']
            assert misptor.v_split('k,,,', sp=',')==['k']
            # number split只推荐用于表单数据
            assert misptor.v_split(123, sp=',')==False
            assert misptor.v_split(-1)==False
            assert misptor.v_split(0)==False
            assert misptor.v_split(1)==False
            # array
            assert misptor.v_split([])==False
            # bool
            assert misptor.v_split(False)==False
            assert misptor.v_split(True)==False
            # null
            assert misptor.v_split(None)==None
        if test == 'list' or test == 'all':
            # other
            assert misptor.v_list('')==None
            # string
            assert misptor.v_list('kk')==False
            # number
            assert misptor.v_list(123)==False
            assert misptor.v_list(0)==False
            assert misptor.v_list(-123.34)==False
            # array
            assert misptor.v_list([])==[]
            assert misptor.v_list([1,2,3])==[1,2,3]
            # bool
            assert misptor.v_list(True)==False
            assert misptor.v_list(False)==False
            # null
            assert misptor.v_list(None)==None
        if test == 'list_int' or test == 'all':
            # array
            assert misptor.v_list_int([])==[]
            assert misptor.v_list_int(['', None])==[]
            assert misptor.v_list_int([1,'2',3])==[1,2,3]

    except AssertionError:
        print(traceback.format_exc())
        print('v_{} test failed'.format(test))
    except:
        print(traceback.format_exc())
        print('other error')
    finally:
        print('v_{} test finish'.format(test))




if __name__ == '__main__':
    import sys
    filename, first_arg = sys.argv
    mode = first_arg or 'all'
    test_valid_func(mode)

