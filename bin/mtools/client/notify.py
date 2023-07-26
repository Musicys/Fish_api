import json
import config
import logging
import traceback

from requests import post

from mtools.base.httpclient import RequestsClient
from mtools.resp.define import PLAT_API
from mtools.base.domain import kv

log = logging.getLogger()


def publish(app_code, event_code, content):
    """运维平台消息订阅发布"""

    PLAT_API = kv.gv(key='PLAT_API') or 'http://127.0.0.1:7800'

    RequestsClient().post(
        url=f'{PLAT_API}/devplat/msg/publish',
        params={
            'app_code': app_code,
            'event_code': event_code,
            'content': json.dumps(content)
        }
    )


def user_notify(userid, notify_type, title, content):
    """运维平台发送消息给用户"""

    PLAT_API = kv.gv(key='PLAT_API') or 'http://127.0.0.1:7800'

    RequestsClient().post(
        url=f'{PLAT_API}/devplat/user/notify',
        params={
            'to_user_id': userid,
            'notify': notify_type,
            'subject': title,
            'content': content,
        }
    )


def notify_input(app_code, subscr_type, title, content, notify_judge, white_list):
    """发送消息通知给平台来转发给关注用户
    params:
        app_code: 应用代码
        subscr_type: 订阅类型
        title: 标题
        content: 内容
        notify_judge: 判断通知是否要发送的控制字符串
        white_list: 此次不通知的用户白名单

    """

    RequestsClient().post(
        url=f'{PLAT_API}/devplat/notify/input',
        params={
            'app_code': app_code,
            'subscr_type': subscr_type,
            'title': title,
            'content': content,
            'notify_judge': notify_judge,
            'white_list': white_list,
        }
    )
