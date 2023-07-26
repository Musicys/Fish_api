import json
import logging
import datetime

from mtools.resp import success
from mtools.resp.define import DTM_FMT
from mtools.resp.excepts import ParamError
from mtools.utils.valid import is_valid_json
from mtools.utils.check import check
from mtools.base.handler import BuildHandler
from mtools.web.validator import F, T_STR, T_INT

from common.define import OrdersDefine

from domain.menu import MenuDomain
from domain.pool import PoolDomain
from domain.orders import OrdersDomain


log = logging.getLogger()


class TradeCreate(BuildHandler):

    _check_fields = [
        F('userid', T_INT, True),
        F('menu', T_STR, True),
    ]

    @check('must')
    def POST(self):

        userid = self.data['userid']

        if not is_valid_json(self.data['menu']):
            raise ParamError("套餐内容无法解析")

        menu = json.loads(self.data['menu'])
        now = datetime.datetime.now().strftime(DTM_FMT)

        # 创建订单
        trade_amt = menu['price']
        pledge_amt = menu['pledge']

        trade_id = OrdersDomain().create(
            trade_amt=trade_amt,
            pledge_amt=pledge_amt,
            menu=self.data['menu'],
            userid=userid,
            trade_time=now,
            state=OrdersDefine.INIT
        )

        # 调用微信支付
        return success({"trade_id": trade_id})
