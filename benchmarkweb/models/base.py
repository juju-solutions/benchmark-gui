import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
)


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=sa.func.now())
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

Base = declarative_base(cls=Base)
