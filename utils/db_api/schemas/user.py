from sqlalchemy import BigInteger, Column, String, sql, Integer, ForeignKey, DateTime, Date, UniqueConstraint, \
    ForeignKeyConstraint
from utils.db_api.db_gino import TimedBaseModel
from loader import db
from sqlalchemy.orm import relationship


class User(TimedBaseModel):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    t_username = Column(String(40))
    t_url = Column(String(80))
    t_fullname = Column(String(150))

    tasks = relationship('Task', back_populates='user', cascade='all, delete-orphan')

    __table_args__ = (UniqueConstraint('chat_id', 'user_id', name='_chat_user_uc'),)  # Составной уникальный индекс


class Task(TimedBaseModel):
    __tablename__ = 'tasks'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
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

    user = relationship('User', back_populates='tasks')

    __table_args__ = (ForeignKeyConstraint(['chat_id', 'created_by'], ['users.chat_id', 'users.user_id']),)