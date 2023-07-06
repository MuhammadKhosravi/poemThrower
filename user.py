from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

class User(declarative_base()):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    username = Column(String(50))
