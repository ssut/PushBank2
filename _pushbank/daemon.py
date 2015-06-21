import asyncio
import copy
import inspect
import json
import os
import sys
from datetime import datetime
from importlib import import_module

from _pushbank.logger import logger
from _pushbank.models import *

class PushBank:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.accounts = []
        self.banks = {}
        self.plugins = None
        self.interval = 5
        self.basepath = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..'))

        self._loop = None

    @asyncio.coroutine
    def execute(self, loop):
        self._loop = loop
        res = self.reload()
        if not res: return
        asyncio.Task(self._update())
        while 1:
            logger.debug('새로운 업데이트가 뜨기를 기다리고 있습니다.')
            update = yield from self.queue.get()
            asyncio.async(self._process(update))

    def reload(self):
        confpath = os.path.join(self.basepath, 'config.json')
        conf = {}
        try:
            with open(confpath, 'r') as fd:
                conf = fd.read()
            self.conf = conf = json.loads(conf)
        except:
            logger.error('설정파일을 불러오지 못했습니다.')
            return 0
        else:
            logger.setLevel(self.conf.get('loglevel', 10))
            self.interval = self.conf.get('interval', 5)

        self.plugins = {}
        for name, params in self.conf.get('plugins').items():
            module = '_pushbank.plugins.{}'.format(name)
            try:
                plugin = import_module(module)
            except ImportError:
                logger.warning('"{}" 플러그인을 불러오지 못했습니다.'.format(name))
            else:
                _, cls = inspect.getmembers(plugin,
                    lambda member: inspect.isclass(member) and \
                                   member.__module__ == module)[0]
                instance = cls(options=params)
                self.plugins[name] = instance
                logger.info('"{}" 플러그인을 불러왔습니다.'.format(name))

        for name, params in self.conf.get('accounts').items():
            bank_name = params.get('bank')
            try:
                if bank_name not in self.banks:
                    module = '_pushbank.banks.{}'.format(bank_name)
                    bank = import_module(module)
                    self.banks[bank_name] = bank
            except ImportError:
                logger.error('{}: 지원하지 않는 은행입니다. ({})'.format(
                    name, bank_name))
            else:
                account = params
                account['name'] = name
                for plugin, _ in account.get('plugins').copy().items():
                    if plugin not in self.plugins:
                        logger.warn('"{}" 플러그인은 로드되지 않은 플러그인입니다.'.format(
                            plugin))
                        del account['plugins'][plugin]
                self.accounts.append(account)
                logger.info('"{}" 계좌({})를 리스트에 등록했습니다.'.format(
                    name, bank_name))

        logger.info('설정파일을 불러왔습니다.')
        return 1

    @asyncio.coroutine
    def _update(self):
        logger.debug('은행에서 데이터를 가져오는 작업을 시작합니다. (주기: {}초)'.format(
            self.interval))
        while 1:
            for account in self.accounts:
                name = account.get('name')
                bank_name = account.get('bank')
                bank = self.banks[bank_name]
                query = copy.deepcopy(account)
                summary = '"{}" 계좌({})'.format(name, bank_name)
                del query['plugins'], query['bank'], query['name']
                try:
                    result = yield from bank.query(**query)
                    if 'balance' not in result:
                        raise ValueError()
                except:
                    logger.warning('{}의 정보를 가져오지 못했습니다.'.format(summary))
                    continue
                balance = result['balance']
                # 잔액 비교
                acc, created = Account.get_or_create(
                    account=name, defaults={'balance': balance})
                if created:
                    logger.info(('{}의 초기 정보를 생성했습니다. ' + \
                        '다음 잔액 변동부터 PushBank가 작동합니다.').format(summary))
                if acc.balance != balance:
                    logger.info('{}의 잔액에 변동이 있습니다.'.format(summary))
                    acc.balance = balance
                    acc.save()
                    data = {
                        'account': acc,
                        'data': result,
                    }
                    yield from self.queue.put(data)
            yield from asyncio.sleep(self.interval)

    @asyncio.coroutine
    def _process(self, update):
        account, data = update.get('account'), update.get('data')



