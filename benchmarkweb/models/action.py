import datetime

import dateutil.parser
import humanize
import pytz
import yaml

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from .base import Base
from ..lib import bundler


def date_str(d):
    return str(d) if d else None


def str_date(s):
    return dateutil.parser.parse(s) if s else None


class Action(Base):
    environment_id = Column(Integer, ForeignKey('environment.id'))

    uuid = Column(String)
    data = Column(JSON)  # straight from juju api
    metrics = Column(JSON)
    profile = Column(JSON)
    bundle = Column(String)
    metrics_updated_at = Column(DateTime(timezone=True))
    profile_updated_at = Column(DateTime(timezone=True))

    tags = relationship("Tag", cascade="all, delete-orphan")
    graphs = relationship("Graph", cascade="all, delete-orphan")

    @classmethod
    def from_data(cls, data):
        o = cls(data=data)
        o.uuid = o.get_uuid()
        return o

    def to_dict(self):
        d = {}
        d.update(self.data)
        d['data'] = self.data
        d['uuid'] = self.uuid
        d['unit'] = self.unit
        d['duration'] = str(self.duration or '')
        d['service'] = self.service
        d['name'] = self.name
        d['started'] = self.started
        d['bundle'] = self.bundle
        d['profile'] = self.profile
        d['metrics'] = self.metrics
        d['metrics_updated_at'] = date_str(self.metrics_updated_at)
        d['profile_updated_at'] = date_str(self.profile_updated_at)
        d['graphs'] = {
            g.uuid: g.to_dict()
            for g in self.graphs
        }
        d['tags'] = [
            t.name for t in self.tags
        ]
        d['environment'] = (self.environment.to_dict(shallow=True)
                            if self.environment else None)

        return d

    @classmethod
    def from_dict(cls, d):
        from . import Tag, Graph

        o = cls(
            uuid=d['uuid'],
            data=d['data'],
            metrics=d['metrics'],
            profile=d['profile'],
            bundle=d['bundle'],
            metrics_updated_at=str_date(d['metrics_updated_at']),
            profile_updated_at=str_date(d['profile_updated_at']),
        )
        o.tags = [Tag(name=t) for t in d['tags']]
        o.graphs = [Graph.from_dict(g) for g in d['graphs'].values()]
        return o

    def to_submission(self):
        """Return a json object suitable for submitting to cloud-benchmarks.org

        """
        if not self.bundle:
            return None

        d = {
            'version': '1.0',
            'action': self.data,
            'environment': self.environment.to_submission(),
            'bundle': yaml.safe_load(self.bundle),
        }
        return d

    def is_current(self, dt):
        """Return True if action is complete and dt is greater than or equal
        to the action stop datetime.

        """
        return (self.stop and dt) and (dt >= self.stop)

    def set_bundle(self, api):
        b = bundler.get_bundle(api, as_yaml=False)
        b = b.values()[0]
        b = trim_bundle(b, self.service)
        self.bundle = yaml.safe_dump(b, default_flow_style=False)
        return self.bundle

    @property
    def benchmark_name(self):
        return '{}:{}'.format(self.service, self.name)

    @property
    def service(self):
        return '-'.join(self.data['action']['receiver'].split('-')[1:-1])

    @property
    def name(self):
        return self.data['action']['name']

    @property
    def status(self):
        return self.data['status']

    @property
    def start(self):
        return self._date('started')

    @property
    def started(self):
        start = self.start
        if not start and self.status in ['pending', 'running', 'canceling']:
            start = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        return start.strftime("%Y-%m-%dT%H:%M:%SZ") if start else None

    @property
    def stop(self):
        if not self.start:
            return None

        if not self._date('completed') or self._date('completed') < self.start:
            return None

        return self._date('completed')

    def _date(self, key):
        date = self.data.get(key)
        if date == '0001-01-01T00:00:00Z':
            return None
        return dateutil.parser.parse(date) if date else None

    @property
    def duration(self):
        start, stop = self.start, self.stop
        if start and stop:
            return stop - start
        return None

    @property
    def human_start(self):
        if not self.start:
            return None

        t = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        return humanize.naturaltime(t - self.start)

    @property
    def human_stop(self):
        if not self.stop:
            return None

        t = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        return humanize.naturaltime(t - self.stop)

    @property
    def tag(self):
        return self.data['action']['tag']

    def get_uuid(self):
        return self.tag[len('action-'):]

    @property
    def receiver(self):
        return self.data['action']['receiver']

    @property
    def parameters(self):
        return self.data['action'].get('parameters', {})

    @property
    def unit(self):
        return '/'.join(self.receiver[len('unit-'):].rsplit('-', 1))

    @property
    def results(self):
        return self.data.get('output', {}).get('results', {})


def trim_bundle(d, svc):
    rels = d['relations']
    svcs = d['services']

    def get_descendants(svc, rels):
        found = False

        if svc in ('collectd', 'cabs', 'cabs-collector', 'benchmark-gui'):
            raise StopIteration

        for rel in rels:
            a, b = rel
            if svc in (a, b):
                found = True
                child = a if svc == b else b
                new_rels = rels[:]
                new_rels.remove(rel)
                yield child
                for descendant in get_descendants(child, new_rels):
                    yield descendant

        if not found:
            raise StopIteration

    services = [svc] + list(get_descendants(svc, rels[:]))
    for s in svcs.keys():
        if s not in services:
            del svcs[s]
    for r in rels[:]:
        a, b = r
        if a not in services or b not in services:
            rels.remove(r)
    return d
