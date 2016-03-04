import asyncio
import json
from datetime import datetime, timedelta

import requests

from bs4 import BeautifulSoup

en_name = 'kbstar'
name = u'국민은행'

_session = requests.Session()
_url = 'https://obank.kbstar.com/quics?asfilecode=524517'
_kst_timezone = timezone(timedelta(hours=9), 'KST')
@asyncio.coroutine
def query(account, password, resident, username):
    """
    국민은행 계좌 잔액 빠른조회. 빠른조회 서비스에 등록이 되어있어야 사용 가능.
    빠른조회 서비스: https://obank.kbstar.com/quics?page=C018920

    account  -- 계좌번호 ('-' 제외)
    password -- 계좌 비밀번호 (숫자 4자리)
    resident -- 주민등록번호 끝 7자리
    username -- 인터넷 뱅킹 ID (대문자)
    """

    if len(password) != 4 or not password.isdigit():
        raise ValueError("password: 비밀번호는 숫자 4자리여야 합니다.")

    if len(resident) != 7 or not resident.isdigit():
        raise ValueError("resident: 주민등록번호 끝 7자리를 입력해주세요.")

    params = {
        '다음거래년월일키': '',
        '다음거래일련번호키': '',
        '계좌번호': account,
        '비밀번호': password,
        '조회시작일': (datetime.now(_kst_timezone) - timedelta(days=14)).strftime('%Y%m%d'),
        '조회종료일': datetime.now(_kst_timezone).strftime('%Y%m%d'),
        '주민사업자번호': '000000' + resident,
        '고객식별번호': username.upper(),
        '응답방법': '2',
        '조회구분': '2',
        'USER_TYPE': '02',
        '_FILE_NAME': 'KB_거래내역빠른조회.html',
        '_LANG_TYPE': 'KOR'
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
        balance = data.select('table table:nth-of-type(1)' +
                              ' tr:nth-of-type(3) td')[-1].text
        balance = int(balance.replace(',', ''))
        history = [
            [y.text.strip() for y in x.select('td')]
            for x in
            data.select('table table:nth-of-type(2) tr[align="center"]')
        ]

        '''
        순서:
            거래일, 적요, 의뢰인/수치인, 내통장표시, 출금금액, 입금금액, 잔액, 취급점, 구분
        '''

        d['balance'] = balance
        d['history'] = [{
            'date': datetime.strptime(x[0], '%Y.%m.%d%H:%M:%S').date(),
            'type': x[1],
            'depositor': x[2],
            'pay': int(x[4].replace(',', '')),
            'withdraw': int(x[5].replace(',', '')),
            'balance': int(x[6].replace(',', '')),
            'distributor': x[7],
        } for x in history]

    return d
