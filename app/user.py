from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    first_name = Column(String(50))
    last_name = Column(String(50))
    user_id = Column(String(50), primary_key=True)
    chat_id = Column(String(50))
    favorite_poet = Column(String(10), default="1")


def get_base():
    return Base
