import asyncio
import json
from datetime import datetime, timezone, timedelta

import requests

from bs4 import BeautifulSoup

en_name = 'hana'
name = u'하나은행'

_session = requests.Session()
_url = 'https://open.hanabank.com/quick_service/inquiryAcct02_01.do'
@asyncio.coroutine
def query(account, password, resident):
    """
    하나은행 계좌 잔액 빠른조회. 빠른조회 서비스에 등록이 되어있어야 사용 가능.
    빠른조회 서비스:
    https://open.hanabank.com/flex/quick/quickService.do?oid=quickservice

    account  -- 계좌번호 ('-' 제외)
    password -- 계좌 비밀번호 (숫자 4자리)
    resident -- 주민등록번호 앞 6자리
    """

    if len(password) != 4 or not password.isdigit():
        raise ValueError("password: 비밀번호는 숫자 4자리여야 합니다.")

    if len(resident) != 6 or not resident.isdigit():
        raise ValueError("resident: 주민등록번호 앞 6자리를 입력해주세요.")

    params = {
        'ajax': 'true',
        'acctNo': account,
        'acctPw': password,
        'bkfgResRegNo': resident,
        'curCd': '',
        'inqStrDt': (datetime.now() - timedelta(days=14)).strftime('%Y%m%d'),
        'inqEndDt': datetime.now().strftime('%Y%m%d'),
        'rvSeqInqYn': 'Y',
        'rcvWdrwDvCd': '',
        'rqstNcnt': '30',
        'maxRowCount': '700',
        'rqstPage': '1',
        'acctType': '01',
        'language': 'KOR'
    }

    try:
        r = _session.get(_url, params=params, timeout=10)
        data = r.text
        success = True
    except:
        success = False

    d = {
        'success': success,
        'account': account,
    }
    if success:
        data = data.replace('&nbsp;', '')
        data = BeautifulSoup(data)
        balance = data.select('table.tbl_col01' +
                              ' tr:nth-of-type(2) td')[0].text.strip()
        balance = int(balance.replace(',', ''))
        history = [
            [y.text.strip() for y in x.select('td')]
            for x in data.select('table.tbl_col01')[1].select('tbody tr')
        ]

        '''
        순서:
            거래일, 구분, 적요, 입금액, 출금액, 잔액, 거래시간, 거래점
        '''

        d['balance'] = balance
        d['history'] = [{
            'date': datetime.strptime('{0},{1}'.format(x[0], x[6]),
                                      '%Y-%m-%d,%H:%M').date(),
            'type': x[1],
            'depositor': x[2],
            'withdraw': int(x[3].replace(',', '') if x[3] else '0'),
            'pay': int(x[4].replace(',', '') if x[4] else '0'),
            'balance': int(x[5].replace(',', '')),
            'distributor': x[7],
        } for x in history]

    return d
