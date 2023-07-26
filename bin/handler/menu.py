import logging

from mtools.resp import success
from mtools.utils.check import check
from mtools.base.handler import BuildHandler
from mtools.web.validator import F, T_STR, T_INT

from domain.menu import MenuDomain
from domain.pool import PoolDomain


log = logging.getLogger()


class MenuList(BuildHandler):

    @check('must')
    def GET(self):

        list_config = {'source': 'fish.menu'}
        data = self.listblr.build(list_config, self.data)

        pool_ids = [i['pool_id'] for i in data['list']]
        id_pool_map = PoolDomain().gets(dict_key='id', id=pool_ids)

        for i in data['list']:
            pool_id = i['pool_id']
            i['pool'] = id_pool_map.get(pool_id) or {}

        return success(data)


class MenuEdit(BuildHandler):

    _check_fields = [
        F('menu_id', T_INT, True),
        F('fish_pool_id', T_INT, True),
        F('duration', T_INT, True),
        F('pledge', T_INT, True),
        F('price', T_INT, True),
    ]

    @check('must')
    def POST(self):

        self.data['id'] = self.data.pop('menu_id')
        MenuDomain().modify('id', **self.data)
        return success({})


class MenuCreate(BuildHandler):

    _check_fields = [
        F('fish_pool_id', T_INT, True),
        F('duration', T_INT, True),
        F('pledge', T_INT, True),
        F('price', T_INT, True),
    ]

    @check('must')
    def POST(self):

        menu_id = MenuDomain().create(**self.data)
        return success({"menu_id": menu_id})
