import asyncio
import os
import json

import requests
from jinja2 import Environment, FileSystemLoader

from _pushbank.classes import Plugin
from _pushbank.logger import logger

class PushoverPlugin(Plugin):
    URL = 'https://api.pushover.net/1/messages.json'

    def __init__(self, **kwargs):
        super(PushoverPlugin, self).__init__(**kwargs)

        self.agent = requests.Session()
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_pushover')
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
        user = param.get('user')
        token = param.get('token')
        content = self.template.render(**history.as_dict())
        data = {
            'user': user,
            'token': token,
            'title': title,
            'message': content,
        }
        r = self.agent.post(self.URL, data=data)
        if r.status_code == 200:
            logger.info('"{}" 계좌의 내역을 성공적으로 Pushover로 발송했습니다. ({})'.format(
                account.account, p))
