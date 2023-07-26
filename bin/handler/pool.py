import logging

from mtools.resp import success
from mtools.utils.check import check
from mtools.base.handler import BuildHandler

from mtools.web.validator import F, T_STR, T_INT

from domain.pool import PoolDomain


log = logging.getLogger()


class PoolList(BuildHandler):

    _check_fields = [
        F('name', T_STR),
    ]

    @check('must')
    def GET(self):

        list_conf = {
            'source': 'fish.pool',
            'rules': ['name']
        }

        data = self.listblr.build(list_conf, self.data)

        return success(data)


class PoolCreate(BuildHandler):

    _check_fields = [
        F('name', T_STR, True),
        F('description', T_STR, default=''),
    ]

    @check('must')
    def POST(self):

        pool_id = PoolDomain().create(**self.data)
        return success({'pool_id': pool_id})


class PoolEdit(BuildHandler):

    _check_fields = [
        F('pool_id', T_INT, True),
        F('name', T_STR, True),
        F('description', T_STR, True),
    ]

    @check('must')
    def POST(self):
        self.data['id'] = self.data.pop('pool_id')
        PoolDomain().modify(modify_key="id", **self.data)
        return success({})
