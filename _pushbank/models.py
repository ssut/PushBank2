import datetime

from peewee import *

db = SqliteDatabase('database.db', threadlocals=True)

class BaseModel(Model):
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

class Account(BaseModel):
    account = CharField(unique=True, max_length=20)
    balance = BigIntegerField()

class History(BaseModel):
    account = ForeignKeyField(Account, related_name='histories')
    date = DateField(index=True)
    type = CharField(max_length=16)
    depositor = CharField(max_length=20)
    pay = IntegerField()
    withdraw = IntegerField()
    balance = BigIntegerField()
    distributor = CharField(max_length=20)

db.connect()
db.create_tables([Account, History], True)
