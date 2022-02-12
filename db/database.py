from peewee import SqliteDatabase
from settings import db_connect

db = SqliteDatabase(db_connect)
