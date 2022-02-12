from peewee import (
    Model,
    AutoField,
    CharField,
    DateField,
    IntegerField,
)
from .database import db


class Income(Model):
    id = AutoField()
    name = CharField()
    amount_of_money = IntegerField()
    date = DateField()

    class Meta:
        database = db
