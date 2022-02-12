from .database import db
from .income import Income
from .expense import Expense

db.create_tables([
    Income,
    Expense,
])
