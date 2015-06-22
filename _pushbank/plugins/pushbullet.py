import asyncio

from _pushbank.classes import Plugin

class PushBulletPlugin(Plugin):
    @asyncio.coroutine
    def execute(self, account, history, params=[]):
        pass
