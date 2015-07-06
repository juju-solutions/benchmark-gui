from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
)

from .base import Base
from .action import Action  # noqa


class Environment(Base):
    uuid = Column(String)
    name = Column(String)
    provider_type = Column(String)
    default_series = Column(String)
    region = Column(String)

    actions = relationship(
        "Action", backref="environment", cascade="all, delete-orphan")
    services = relationship(
        "Service", backref="environment", cascade="all, delete-orphan")
    units = relationship(
        "Unit", backref="environment", cascade="all, delete-orphan")

    def to_dict(self, shallow=False):
        d = {}
        d['uuid'] = self.uuid
        d['name'] = self.name
        d['provider_type'] = self.provider_type
        d['default_series'] = self.default_series
        d['region'] = self.region
        if not shallow:
            d['actions'] = {
                a.uuid: a.to_dict()
                for a in self.actions
            }
            d['services'] = {
                s.name: s.to_dict()
                for s in self.services
            }
            d['units'] = {
                u.name: u.to_dict()
                for u in self.units
            }
        return d

    def to_submission(self):
        d = {}
        d['uuid'] = self.uuid
        d['cloud'] = ''
        d['provider_type'] = self.provider_type
        d['region'] = self.region
        return d


class Service(Base):
    environment_id = Column(Integer, ForeignKey('environment.id'))

    name = Column(String)
    data = Column(JSON)

    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['data'] = self.data
        return d


class Unit(Base):
    environment_id = Column(Integer, ForeignKey('environment.id'))

    name = Column(String)
    data = Column(JSON)

    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['data'] = self.data
        return d


class Comparison(Base):
    uuid = Column(String)
    graphs = relationship("Graph", cascade="all, delete-orphan")

    def to_dict(self):
        d = {}
        d['uuid'] = self.uuid
        d['graphs'] = {
            g.uuid: g.to_dict()
            for g in self.graphs
        }
        return d


class Graph(Base):
    action_id = Column(Integer, ForeignKey('action.id'))
    comparison_id = Column(Integer, ForeignKey('comparison.id'))

    uuid = Column(String)
    label = Column(String)
    data = Column(JSON)

    def to_dict(self):
        d = {}
        d.update(self.data)
        d['uuid'] = self.uuid
        d['label'] = self.label
        d['data'] = self.data
        return d

    @classmethod
    def from_dict(cls, d):
        o = cls(
            uuid=d['uuid'],
            label=d['label'],
            data=d['data'],
        )
        return o


class Tag(Base):
    action_id = Column(Integer, ForeignKey('action.id'))

    name = Column(String)
