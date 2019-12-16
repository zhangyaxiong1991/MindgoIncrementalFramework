# coding:utf-8
import json
import requests
import re
import datetime


MINDGO_POLICY_UPDATE = 'http://quant.10jqka.com.cn/platform/algorithms/update/?callback=jQuery18302509040414615056_1576422435431'
MINDGO_POLICY_RUN = 'http://quant.10jqka.com.cn/platform/backtest/run/'

class Mindgo:
    def __init__(self, policy_ids, cookie_user, start, end):
        self.cookie_user = cookie_user
        self.policy_ids = policy_ids
        self.start = datetime.datetime.strptime(start, '%Y-%m-%d')
        self.end = datetime.datetime.strptime(end, '%Y-%m-%d')
        self.frequency = 'DAILY'

    def _check_response(self, response):
        ret = json.loads(response.content)
        if not response.status_code == 200:
            raise Exception('reqauest failed: {}'.format(response.status_code))
        if ret['errorcode']:
            raise Exception('update failed: {}'.format(ret['errormsg']))

    def update_policy_content(self, policy_id, content):
        data = {
            'algoId': policy_id,
            'algoCode': content,
            'isajax': 1,
            'datatype': 'json'
        }

        cookies = {
            'user': self.cookie_user
        }

        response = requests.post(MINDGO_POLICY_UPDATE, data=data, cookies=cookies)
        self._check_response(response)

    def run_policy(self, policy_id):
        data = {
            'beginDate': self.start.strftime('%Y-%m-%d'),
            'endDate': self.end.strftime('%Y-%m-%d'),
            'frequency': self.frequency,
            'capitalBase': 100000,
            'style': 'NORMAL',
            'algoId': policy_id,
            'isajax': 1,
            'datatype': 'json'
        }

        cookies = {
            'user': self.cookie_user
        }

        response = requests.post(MINDGO_POLICY_RUN, data=data, cookies=cookies)
        self._check_response(response)

    def distribute(self, count, content):
        policy_num = len(self.policy_ids)
        if not policy_num:
            return
        all_content = []
        step = int(count / policy_num)
        extra_num = count % policy_num
        start = 0
        for i in range(policy_num):
            end = start + step
            if extra_num > 0:
                end += 1
            step_content = re.sub(r'{start}', str(start), content)
            step_content = re.sub(r'{end}', str(end), step_content)
            all_content.append(step_content)

            start = end
            extra_num -= 1

        for i, step_content in enumerate(all_content):
            self.update_policy_content(self.policy_ids[i], step_content)
            self.run_policy(self.policy_ids[i])
