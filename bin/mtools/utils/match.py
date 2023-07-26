'''Msg Match'''

import json
import logging
import datetime
import traceback

from mtools.utils.ruler import Ruler

from mtools.base.domain import MatchRules, SubscripitonRule
from mtools.define.subscr import MATCH_OPEN, STATE_OPEN, RULE_MATCH
from mtools.resp.define import DTM_FMT

from mtools.client.task import task_call

log = logging.getLogger()


class EventMsgMatch(object):
    """事件数据字典匹配消息规则"""

    def __init__(self, group_code, event_data, app_code=None):
        self.group_code = group_code
        self.event_data = event_data
        self.app_code = app_code

    def match(self, with_rule=False):
        """匹配"""

        # 消息匹配项
        if self.app_code:
            subscr = SubscripitonRule().gets(
                group_code=self.group_code,
                app_code=self.app_code,
                state=STATE_OPEN,
                subscr_detail_format=RULE_MATCH
            )
        else:
            subscr = SubscripitonRule().gets(
                group_code=self.group_code,
                state=STATE_OPEN,
                subscr_detail_format=RULE_MATCH
            )

        if not subscr:
            return {}

        if not self.app_code:
            self.app_code = subscr[0]['app_code']

        scode_subscr_map = {i['subscr_type_code']: i for i in subscr}
        subscr_type_codes = list(scode_subscr_map.keys())

        # 取出匹配的规则
        rule_items = MatchRules().gets(
            subscr_type_code=subscr_type_codes,
            state=MATCH_OPEN
        )
        if not rule_items:
            return {}

        rules = []
        rid_rule_map = {}
        for i in rule_items:
            try:
                rule = {
                    'id': i['id'],
                    'rule': json.loads(i['trigger_rules']),
                    'result': {
                        'msg_level': str(i['msg_level']),
                        'subscr_type_code': str(i['subscr_type_code'])
                    }
                }
            except Exception:
                log.warn(traceback.format_exc())
            rules.append(rule)
            rid_rule_map[i['id']] = rule['rule']

        # 进行匹配
        r = Ruler(rules)
        matchs = r.check(self.event_data, 3)

        mcode_level_map = {}
        for i in matchs:

            scode = i[2]['subscr_type_code']
            msg_level = i[2]['msg_level']
            hit_rules = rid_rule_map[i[1]]

            # 已经触发的消息level高则低的就不发送了
            if with_rule:
                hit_sub = mcode_level_map.get(scode) or {}
                if hit_sub.get('msg_level', '0') > msg_level:
                    continue
                mcode_level_map[scode] = {
                    'msg_level': msg_level,
                    'rules': hit_rules,
                    'subscr_name': scode_subscr_map[scode]['subscr_type_name'],
                }
            else:
                if mcode_level_map.get(scode, '0') > msg_level:
                    continue
                mcode_level_map[scode] = msg_level

        return mcode_level_map

    def match_and_msg(self):
        """匹配并且发送消息"""
        mcode_level_map = self.match(True)

        now = datetime.datetime.now().strftime(DTM_FMT)

        log.warn(mcode_level_map)
        for mcode, mrule in mcode_level_map.items():

            # 组装发送消息的内容
            trigger_data_list = []
            trigger_rule_list = []
            for r in mrule['rules']:
                trigger_key = r[0]
                trigger_keys = trigger_key.split('.')
                trigger_value = self.event_data
                for i in trigger_keys:
                    trigger_value = trigger_value[i]

                trigger_data_list.append(f'{trigger_key} = {trigger_value}')
                trigger_rule_list.append(' '.join([str(k) for k in r]))

            trigger_data_str = '; '.join(trigger_data_list)
            trigger_rule = ' & '.join(trigger_rule_list)
            content = f'{trigger_data_str}  触发了规则 \r\n {trigger_rule} \r\n 请注意处理'

            # 发送消息
            level = mrule['msg_level']
            title = f"{now} {mrule['subscr_name']}"
            task_call(
                'apps.devplat.message.input',
                (mcode, title, content, level, self.app_code)
            )
