import asyncio
import re
from datetime import datetime, timedelta

import requests

from bs4 import BeautifulSoup

en_name = 'nhbank'
name = u'농협은행'

_session = requests.Session()

def _as_int(text):
    text = re.sub(r'\D', '', text)
    return int(text) if text else 0

def _acquire_tokens():
    response = _session.get('https://banking.nonghyup.com/nhbank.html')
    response = _session.post('https://banking.nonghyup.com/servlet/IPMS0011I.view')

    match = re.search(r'window\["SESSION_TOKEN"\]\s+\=\s+\'(.+?)\'', response.text)
    session_token = match.group(1)

    match = re.search(r'window\["TOKEN"\]\s+\=\s+\'(.+?)\'', response.text)
    token = match.group(1)

    return (session_token, token)

@asyncio.coroutine
def query(account, password, resident):
    """
    농협은행 계좌 잔액 빠른조회. 빠른조회 서비스에 등록이 되어있어야 사용 가능.
    빠른조회 서비스:
    https://banking.nonghyup.com/servlet/IPAM0011I.view

    account  -- 계좌번호 ('-' 제외)
    password -- 계좌 비밀번호 (숫자 4자리)
    resident -- 주민등록번호 앞 6자리
    """

    if len(password) != 4 or not password.isdigit():
        raise ValueError("password: 비밀번호는 숫자 4자리여야 합니다.")

    if len(resident) != 6 or not resident.isdigit():
        raise ValueError("resident: 주민등록번호 앞 6자리를 입력해주세요.")

    tokens = _acquire_tokens()
    start_date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')

    payload = {
        'GjaGbn': '1',
        'InqGjaNbr': account,
        'GjaSctNbr': password,
        'rlno1': resident,
        'InqGbn_2': '2',
        'InqGbn': '1',
        'InqFdt': start_date,
        'InqEndDat': end_date,
        'InqDat': start_date,
        'EndDat': end_date,
        'SESSION_TOKEN': tokens[0],
        'TOKEN': tokens[1],
    }

    try:
        response = _session.post('https://banking.nonghyup.com/servlet/IPMS0012R.frag', data=payload, timeout=10)
        data = response.text
        success = True

        if '<div class="error">' in data: # e.g. maintenance
            success =False
    except:
        success = False

    result = {
        'success': success,
        'account': account,
    }

    if success:
        data = data.replace('<br>', ' ')
        soup = BeautifulSoup(data)

        balance = soup.select('.tb_row tr')[1].select('td')[1].text.strip()
        transactions = [
            [td.text.strip() for td in tr.select('td')]
            for tr in soup.select('#listTable tbody tr')
        ]

        '''
        순서:
            순번, 거래일자, 출금금액, 입금금액, 거래후잔액, 거래내용, 거래기록사항, 거래점
        '''

        result['balance'] = _as_int(balance)
        result['history'] = [{
            'date': datetime.strptime(transaction[1], '%Y/%m/%d %H:%M:%S').date(),
            'withdraw': _as_int(transaction[2]),
            'pay': _as_int(transaction[3]),
            'balance': _as_int(transaction[4]),
            'type': transaction[5],
            'depositor': transaction[6],
            'distributor': transaction[7],
        } for transaction in transactions]

    return result
