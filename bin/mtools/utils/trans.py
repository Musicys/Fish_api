from mtools.base.dbpool import get_connection


def transform(to, id_key, used_keys=None):
    def _(records):
        if to == 'user':
            r = transform_user(id_key, used_keys, records)
        return r
    return _


def transform_user(id_key, used_keys, records):
    ids = [i[id_key] for i in records]
    users = []
    with get_connection('uyu_core') as db:
        users = db.select(
            table = 'auth_user',
            fields = used_keys,
            where = ('id', ('in', ids))
        ) or []
        uid_info_map = {i['id']: i for i in users}
    for i in records:
        info = uid_info_map.get(i[id_key]) or {}
        i.update(info)
