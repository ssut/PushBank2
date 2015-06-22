from datetime import datetime

class Plugin:
    wait = False

    def __init__(self, options={}):
        self._options = options

    @property
    def options(self):
        return self._options

    def format_args(self, account, history):
        transaction_type = '출금' if history.pay > 0 else '입금'
        value = history.withdraw - history.pay
        value_readable = '{:,}'.format(value)
        absvalue = abs(value)
        absvalue_readable = '{:,}'.format(absvalue)
        d = {
            'name': account.account,
            'account_balance': account.balance,
            'balance': history.balance,
            'date': history.date,
            'type': history.type,
            'depositor': history.depositor,
            'pay': history.pay,
            'withdraw': history.withdraw,
            'transaction_type': transaction_type,
            'value': value,
            'value_readable': value_readable,
            'absvalue': absvalue,
            'absvalue_readable': absvalue_readable,
            'distributor': history.distributor,
            'now': datetime.now(),
        }
        return d

