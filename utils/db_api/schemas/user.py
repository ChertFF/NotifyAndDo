from sqlalchemy import BigInteger, Column, String, sql, Integer, ForeignKey, DateTime, Date
from utils.db_api.db_gino import TimedBaseModel
from loader import db

class User(TimedBaseModel):
    __tablename__ = 'users'
    chat_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    t_username = Column(String(40))
    t_url = Column(String(80))
    t_fullname = Column(String(150))

class Task(TimedBaseModel):
    __tablename__ = 'tasks'

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('users.chat_id'))
    created_by = Column(BigInteger, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    deadline = Column(Date, nullable=False)
    notification_date = Column(Date, nullable=False)
    status = Column(String, default='Новая')
    responsible = Column(String, nullable=False)
    closed_at = Column(DateTime)
    closed_by = Column(BigInteger)
    decision_by_close = Column(String)
