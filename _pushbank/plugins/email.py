import asyncio
import os
import smtplib
import traceback
from email.mime.text import MIMEText
from email.header import Header

from jinja2 import Environment, FileSystemLoader

from _pushbank.classes import Plugin
from _pushbank.logger import logger


class EmailPlugin(Plugin):
    def __init__(self, **kwargs):
        super(EmailPlugin, self).__init__(**kwargs)

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_email')
        self.template = Environment(
            loader=FileSystemLoader(path)).get_template('template.html')

    @asyncio.coroutine
    def execute(self, account, history, params=[]):
        for param in params:
            yield from self._execute(account, history, param)

    @asyncio.coroutine
    def _execute(self, account, history, param):
        p = param
        param = self.options[param]
        user, target = param.get('user'), param.get('target')
        title = param.get('title').format(bank_name=account.account)
        params = {
            'server': param.get('server'),
            'port': param.get('port'),
            'user': param.get('user'),
            'passwd': param.get('password'),
            'tls': param.get('tls', False),
        }
        try:
            session = yield from self._smtp_session(**params)
        except Exception as e:
            logger.error(e.strerror)
            return

        content = self.template.render(**history.as_dict())
        corpo = MIMEText(content, 'html', 'utf-8')
        corpo['From'] = user
        corpo['To'] = target
        corpo['Subject'] = Header(title, 'utf-8')
        try:
            session.sendmail(target, [target], corpo.as_string())
        except:
            logger.error('SMTP 서버를 통해 메일을 보내지 못했습니다.')
            traceback.print_exc()
        else:
            logger.info('"{}" 계좌의 내역을 성공적으로 메일을 발송했습니다. ({})'.format(
                account.account, p))


    @asyncio.coroutine
    def _smtp_session(self, server, port, user, passwd, tls):
        session = smtplib.SMTP(server, port)
        session.elho()
        if tls:
            session.starttls()
        try:
            result = session.login(user, passwd)
            if result[0] != 235 and result[0] != 270 and 'Accept' not in result[1]:
                raise Exception('SMTP 서버와의 연결 협상에 실패했습니다.')
            status = session.noop()[0]
            if status != 250:
                raise Exception('SMTP 서버와의 연결이 호스트에 의해 끊어졌습니다.')
        except:
            raise Exception('SMTP 서버 로그인에 실패했습니다.')
        else:
            logger.debug('SMTP 서버에 연결되었습니다.')
        return session
