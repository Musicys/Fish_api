'''builder module of vtools'''

import logging
import traceback
import csv
import io
import openpyxl
import pymysql

from mtools.resp.excepts import ParamError, DevplatException, DBError
from mtools.base.dbpool import get_connection_exception

import config


log = logging.getLogger()


class Builder(object):

    def __init__(self, source):
        self.input = {}
        self.result = {}
        self.source = source
        self.init()

    def init(self, *args, **kw):
        pass

    def before_build(self):
        pass

    def build(self):
        pass

    def after_build(self, ret):
        pass

    def run(self):
        self.before_build()
        ret = self.build()
        self.after_build(ret)
        return ret


class DataBuilder(Builder):

    name = 'datablr'

    _exists = set([
        'after_build', 'before_build', 'build', 'default', 'hand_except_mode', 'init',
        'input', 'k_except_map', 'keys', 'name', 'result', 'run',
        'source', 'values', '_exists', '_get_check_funcs', 'allow_rest', 'add_fields', '_fields', '_field_map'
    ])

    def init(self,
            check_order: list = None,
            allow_rest=False,
            fields=None,
            args=None,
        ):

        self.hand_except_mode = 'raise'
        self.allow_rest = allow_rest
        self.add_fields(fields)
        # 自定义用于校验的数据
        if args is not None:
            self.source['args'] = args

        # 计算出所有定义的数据
        self.keys = self._get_check_funcs()
        self.k_except_map = {}
        if check_order:
            if not isinstance(check_order, list):
                raise ParamError('check order must be a list')
            notin_order_args = set(self.keys) - set(check_order)
            self.keys = check_order + list(notin_order_args)

    def add_fields(self, fields):
        #             field_class must default
        # [ ('userid', Int, True, 3011246)  ]
        self._fields = fields or []
        self._field_map = {i[0]: i[1](i[2], i[3], i[0]) for i in self._fields}

    def _get_check_funcs(self):
        return [i for i in set(dir(self)) - set(self._exists) if not i.startswith('_')] + [i[0] for i in self._fields]

    def default(self, v):
        return v

    def build(self):
        return self._logic_detection()

    def _logic_detection(self):
        '''业务逻辑校验

        功能:
            指定调用业务逻辑函数顺序
            调用每个字段的业务逻辑函数
        其他:

        '''

        values = self.source['args']
        self.process_data = {}

        # 业务逻辑校验(顺序)
        for k in self.keys:

            v = values.get(k)

            # 取出业务逻辑校验函数
            if k in self._field_map:
                field_func = self._field_map[k]
                field_func.value = v
                try:
                    field_func.do()
                except DevplatException as e:
                    # 默认直接raise
                    if self.hand_except_mode == 'raise':
                        raise
                    # store 模式存储所有字段的错误一次返回
                    elif self.hand_except == 'store':
                        self.k_except_map[k] = e
                except Exception:
                    raise
                ret = field_func.value
            else:
                logic_verify_func = getattr(self, k, self.default)


                # 默认None
                ret = None

                # 业务逻辑判断
                try:
                    if not callable(logic_verify_func):
                        raise ParamError(f'check func {k} not existed')
                    ret = logic_verify_func(v)
                except DevplatException as e:
                    # 默认直接raise
                    if self.hand_except_mode == 'raise':
                        raise
                    # store 模式存储所有字段的错误一次返回
                    elif self.hand_except == 'store':
                        self.k_except_map[k] = e
                except Exception:
                    raise

            self.process_data[k] = ret

        if self.allow_rest:
            values.update(self.process_data)
            self.process_data = values

        return self.process_data


class ListBuilder(Builder):
    name = 'listblr'

    _time_args = ['time', 'date', 'sysdtm']
    attr_op_map = {
        'ge': '>=',
        'gt': '>',
        'lt': '<',
        'le': '<=',
        'neq': '!='
    }

    def __init__(self, minfo):
        self.minfo = minfo

    def _limit_to_other(self):
        '''把limit内容解析到dbpool的other'''

        self.group_by = ''
        self.order_by = ''
        self.sort = ''
        for limit_name, limit_value in self.limits.items():
            if limit_name == 'group_by':
                self.group_by = 'group by {}'.format(limit_value)
            if limit_name == 'order_by':
                self.order_by = 'order by {}'.format(limit_value)
            if limit_name == 'sort':
                self.sort = limit_value
        self.other_total = '{} {} {}'.format(self.group_by, self.order_by, self.sort)
        self.other = self.other_total + ' limit {} offset {}'
        # data模式限制长度
        self.other_limit = self.other_total + ' limit {}'
        self.other_offset = self.other_total + ' offset {}'

    def w_key(self, key):
        '''包裹key用``'''
        return '`{}`'.format(key)

    def _value_by_rule_from_data(self, rule, data):
        '''根据rule从数据里面取值并处理'''

        value = data.get(rule)
        if value is None:
            # 时间参数处理
            for i in self._time_args:
                if not rule.endswith(i):
                    continue
                start_time = data.get(f'{rule}_s{i}')
                end_time = data.get(f'{rule}_e{i}')
                if start_time and end_time:
                    value = (start_time, end_time)
        return value

    def _parse_rule(self, rule):
        '''解析带控制属性(fuzzy.nickname)的rule'''

        attr = None
        if '.' in rule:
            attr, rule = rule.split('.')
        return attr, rule

    def escape_fuzzy(self, value, attr):

        for i in ['%', '_']:
            if i in value:
                value = value.replace(i, '\\' + i)
        if attr == 'fuzzy':
            return f'%{value}%'
        elif attr == 'lfuzzy':
            return f'%{value}'
        elif attr == 'rfuzzy':
            return f'{value}%'
        elif attr == 'and_fuzzy':
            return [f'%{i.strip()}%' for i in value.split('|')]

    def _rule_to_where(self, data):
        '''根据rule和value的值自动设置where'''

        self.where = {}

        for rule in self.rules:
            # 解析控制属性
            attr, rule = self._parse_rule(rule)
            # 取值并处理空None
            value = self._value_by_rule_from_data(rule, data)
            if value is None:
                continue
            # 根据属性去定义where的类型
            # attr None
            if attr is None:
                if isinstance(value, list):
                    self.where[rule] = ('in', value)
                else:
                    self.where[rule] = value
            # attr fuzzy
            elif attr.endswith('fuzzy'):
                self.where[rule] = ('like', self.escape_fuzzy(value, attr))
            # attr timein
            elif attr == 'timein':
                self.where[rule] = ('between', value)
            # attr other
            elif attr in self.attr_op_map:
                self.where[rule] = (self.attr_op_map[attr], value)

        # 处理other,加上limit offset
        self.offset = self._offset if self._offset is not None else self._page * self._size
        self.limit = self._size
        self.other = self.other.format(self.limit, self.offset)
        self.other_limit = self.other_limit.format(self.limit)
        self.other_offset = self.other_offset.format(self.offset)

    def _limit_to_where(self):

        for limit_name, limit_value in self.limits.items():
            if not limit_value:
                continue
            if limit_name in ('group_by', 'order_by', 'sort'):
                continue
            if isinstance(limit_value, tuple):
                if len(limit_value) != 2:
                    log.warn('MH> limits setting error {}'.format(limit_value))
                    continue
                value = limit_value[1]
                # ('in', []) 去除这种以及类似情况
                # FIXME
                if not value and value not in (0,):
                    continue

            if limit_name in self.where:
                limit_name = self.w_key(limit_name)
            self.where[limit_name] = limit_value

    def _query_list(self, how='query'):

        if how == 'query':
            other = self.other
        elif how == 'data':
            other = self.other_total
        elif how == 'part':
            other = self.other_limit
        elif how == 'offset':
            other = self.other_offset

        lists = []
        try:
            with get_connection_exception(self.db) as db:
                lists = db.select(
                    table=self.table,
                    fields=self.fields,
                    where=self.where,
                    other=other
                ) or []
        except pymysql.ProgrammingError as e:
            if e[0] == 1146:
                log.warn('table {} not exist'.format(self.table))
                raise DBError(langs['en'].RESPMSG.TABLE_NOT_EXIST)
        except:
            log.warn(traceback.format_exc())
            raise ParamError('Query data failed')
        self.lists = lists
        return self.lists

    def _query_count(self):
        total = []
        try:
            with get_connection_exception(self.db) as db:
                total = db.select(
                    table=self.table,
                    fields='count(*) as total',
                    where=self.where,
                    other=self.group_by
                ) or []
        except pymysql.ProgrammingError as e:
            if e[0] == 1146:
                log.warn('table {} not exist'.format(self.table))
                raise DBError(langs['en'].RESPMSG.TABLE_NOT_EXIST)
        except:
            log.warn(traceback.format_exc())
            raise ParamError('Query data failed')
        self.total = len(total) if self.group_by else total[0]['total']
        return self.total

    def _handle_page(self, data):
        '''处理 分页'''

        if '_page' in data:
            self._page = data['_page']
        elif 'page' in data:
            self._page = data['page']
        else:
            self._page = 0

        if '_size' in data:
            self._size = data['_size']
        elif 'size' in data:
            self._size = data['size']
        elif 'page_size' in data:
            self._size = data.pop('page_size')
        else:
            self._size = 10

        if '_offset' in data:
            self._offset = data['_offset']
        elif 'offset' in data:
            self._offset = data['offset']
        else:
            self._offset = None

        return data

    def build(self, list_args, data, how='query'):

        if 'source' not in list_args:
            raise ParamError('MH> no source in list args')
        self.db, self.table = list_args['source'].split('.')
        self.fields = list_args.get('fields') or '*'
        self.rules = list_args.get('rules') or []
        self.limits = list_args.get('limits') or {}

        data = self._handle_page(data)

        self._limit_to_other()

        self._rule_to_where(data)
        self._limit_to_where()

        page_data_name = getattr(config, 'PAGE_DATA_NAME', 'list')
        page_total_count_name = getattr(config, 'PAGE_TOTAL_COUNT_NAME', 'total_count')
        page_total_page_name = getattr(config, 'PAGE_TOTAL_PAGE_NAME', 'total_page')
        page_no_name = getattr(config, 'PAGE_NO_NAME', 'page_no')
        page_size_name = getattr(config, 'PAGE_SIZE_NAME', 'page_size')

        if how == 'query':
            self.ret = {
                page_data_name: self._query_list(how),
                page_total_count_name: self._query_count(),
                page_no_name: self._page + 1,
                page_size_name: self._size
            }
            self.ret[page_total_page_name] = self.ret[page_total_count_name] // self.ret[page_size_name] + int(bool(
                self.ret[page_total_count_name] % self.ret[page_size_name]))
        elif how == 'data':
            self.ret = self._query_list(how)
        elif how == 'part':
            self.ret = self._query_list(how)
        elif how == 'offset':
            self.ret = {
                page_data_name: self._query_list(how),
                page_total_count_name: self._query_count(),
            }
        else:
            raise ParamError('how: {}, is not allowed'.format(how))
        return self.ret

class ExpoBuilder(Builder):

    name = 'expoblr'

    def init(self):
        self.bio = io.BytesIO()

    def process_data(self, data):
        pass

    def make_name(self):
        pass

    def xlsx(self, head_map, data_list):
        wb = openpyxl.Workbook()
        ws = wb.active
        name_list = []
        key_list = []
        for name, key in head_map:
            name_list.append(name)
            key_list.append(key)
        ws.append(name_list)
        for data in data_list:
            _tmp = []
            for key in key_list:
                _tmp.append(data.get(key) or '')
            ws.append(_tmp)
        wb.save(self.bio)

    def csv(self, head_map, data):
        wr = csv.writer(self.bio)

        name_list = []
        for name, key in head_map:
            name_list.append(name)
        wr.writerow(name_list)
        for data in data_list:
            tmp = []
            for name in name_list:
                tmp.append(data.get(name) or '')
            wr.writerow(tmp)

    def build(self, head_map, data_list, mode='xlsx'):
        '''
        data_list: [{'username': 'abc', 'userid': 123}]
        head_map = [('账号', 'username')]
        '''
        func = getattr(self, mode, None)
        if not func:
            raise ParamError('不支持的导出格式')
        func(head_map, data_list)
        return self.bio.getvalue()


class TransBuilder(Builder):

    name = 'tranblr'

    def build(self, records, **kw):
        trans_map = {}
        dict_map = {}
        for k,v in kw.items():
            if isinstance(v, dict):
                dict_map[k] = v
            else:
                v(records)
        for i in records:
            for k, v in i.items():
                if k in dict_map:
                    i[k] = dict_map[k].get(v) or ''
        return records


builder_map = {
    ListBuilder.name: ListBuilder,
    ExpoBuilder.name: ExpoBuilder,
    TransBuilder.name: TransBuilder,
}
