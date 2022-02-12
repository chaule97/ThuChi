from peewee import (
    Model,
    AutoField,
    CharField,
    DateField,
    IntegerField,
)
from .database import db


class Expense(Model):
    MUST_HAVE = 'MUST_HAVE'
    NICE_TO_HAVE = 'NICE_TO_HAVE'
    WASTED = 'WASTED'

    id = AutoField()
    name = CharField()
    amount_of_money = IntegerField()
    date = DateField()
    type = CharField()

    class Meta:
        database = db
