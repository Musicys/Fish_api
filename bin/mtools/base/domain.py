import json
import pymysql
import logging
import traceback

from mtools.base.dbpool import get_connection

from mtools.resp.excepts import ParamError, DBError


log = logging.getLogger()

DATE_FMT = '%Y-%m-%d'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S'


class Domain(object):

    dbname = 'comistxs'
    table = None

    def __init__(self, source=None):
        self.source = source
        self.load()

    @classmethod
    def manual(cls, dbname, table, source):
        cls.dbname = dbname
        cls.table = table
        return cls(source)

    def load(self):
        pass

    def _table_unq_keys(self):
        with get_connection(self.dbname) as db:
            ret = db.query(f'desc {self.table}', isdict=False)
            log.debug(ret)
            keys = [i[0] for i in ret if i[3] in ('PRI', 'UNI')]
            log.debug(keys)
            if not keys:
                raise DBError(f'无法获取映射数据, {self.table}表没有唯一键或者主键')
            return keys

    def gets(self, *args, dict_key=None, other='', json_fields=None, **kw):

        if args and dict_key and dict_key not in args:
            args.append(dict_key)

        where = {}
        for k, v in kw.items():
            if v is None:
                continue
            if isinstance(v, list):
                where[k] = ('in', v)
            else:
                where[k] = v

        records = []
        with get_connection(self.dbname) as db:
            records = db.select(
                fields = args or '*',
                table = self.table,
                where = where,
                other = other
            ) or []
        if json_fields:
            for record in records:
                for i in json_fields:
                    if not record[i]:
                        continue
                    record[i] = json.loads(record[i])
        if dict_key:
            return {i[dict_key]: i for i in records}
        return records

    def get(self, **kw):
        record = {}
        with get_connection(self.dbname) as db:
            record = db.select_one(
                table = self.table,
                where = kw,
            ) or {}
        return record

    def modify(self, modify_key=None, **kw):
        if not kw:
            return

        where = {}
        if modify_key and modify_key in kw:
            where[modify_key] = kw[modify_key]
            del kw[modify_key]
        else:
            for k in self._table_unq_keys():
                if k in kw:
                    where[k] = kw[k]
            if not where:
                raise DBError('must have a unique key for update')

        with get_connection(self.dbname) as db:
            db.update(self.table, kw, where=where)

    def create(self, **kw):

        try:
            with get_connection(self.dbname) as db:
                db.insert(self.table, values=kw)
                if db.type != 'pymysqlck':
                    last_id = db.last_insert_id()
                else:
                    last_id = 0
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                raise ParamError('插入的数据已经存在')
            else:
                log.warn(traceback.format_exc())
                raise ParamError('写入数据失败')
        return last_id

    def create_dup(self, duplicate_key: list=None, **kw):
        '''因唯一键有重复的数据默认update duplicate key'''

        duplicate = ','.join([f'{i}=values({i})' for i in duplicate_key or []])
        other = 'on duplicate key update utime=now()'
        if duplicate:
            other = other + ',' + duplicate

        try:
            with get_connection(self.dbname) as db:
                db.insert(self.table, values=kw, other=other)
                if db.type != 'pymysqlck':
                    last_id = db.last_insert_id()
                else:
                    last_id = 0
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                raise ParamError('插入的数据已经存在')
            else:
                log.warn(traceback.format_exc())
                raise ParamError('写入数据失败')
        return last_id

    def creates(self, datas):

        try:
            with get_connection(self.dbname) as db:
                db.insert_list(self.table, values_list=datas)
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                raise ParamError('插入的数据已经存在')
            else:
                log.warn(traceback.format_exc())
                raise ParamError('写入数据失败')
        except Exception:
                raise ParamError('写入数据失败')

    def create_dups(self, duplicate_key: list=None, values_list: list=None, **kw):
        '''因唯一键有重复的数据默认update duplicate key'''

        duplicate = ','.join([f'{i}=values({i})' for i in duplicate_key or []])
        other = 'on duplicate key update utime=now()'
        if duplicate:
            other = other + ',' + duplicate

        try:
            with get_connection(self.dbname) as db:
                db.insert_list(
                    table = self.table,
                    values_list = values_list,
                    other=other
                )
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                raise ParamError('插入的数据已经存在')
            else:
                log.warn(traceback.format_exc())
                raise ParamError('写入数据失败')

    def delete(self, **kw):

        with get_connection(self.dbname) as db:
            db.delete(
                table = self.table,
                where = kw,
            )




