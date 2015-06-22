import asyncio
import os
import json

import requests
from jinja2 import Environment, FileSystemLoader

from _pushbank.classes import Plugin
from _pushbank.logger import logger

class PushBulletPlugin(Plugin):
    URL = 'https://api.pushbullet.com/v2/pushes'

    def __init__(self, **kwargs):
        super(PushBulletPlugin, self).__init__(**kwargs)

        self.agent = requests.Session()
        self.agent.headers.update({'Content-Type': 'application/json'})
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_pushbullet')
        self.template = Environment(
            loader=FileSystemLoader(path)).get_template('template.txt')

    @asyncio.coroutine
    def execute(self, account, history, params=[]):
        for param in params:
            yield from self._execute(account, history, param)

    @asyncio.coroutine
    def _execute(self, account, history, param):
        p = param
        param = self.options[param]
        user, target = param.get('user'), param.get('target')
        title = param.get('title').format(**self.format_args(account, history))
        token = param.get('token')
        content = self.template.render(**history.as_dict())
        data = {
            'type': 'note',
            'title': title,
            'body': content,
        }
        r = self.agent.post(self.URL, data=json.dumps(data),
                            headers={'Authorization': 'Bearer {}'.format(token)})
        if r.status_code == 200:
            logger.info('"{}" 계좌의 내역을 성공적으로 PushBullet으로 발송했습니다. ({})'.format(
                account.account, p))
