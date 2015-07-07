from . import models as M


class DB(object):
    def __init__(self, session, settings):
        self.db = self.session = session
        self.env = self.get_env(settings)

    @classmethod
    def from_request(cls, request):
        return cls(request.db, request.registry.settings)

    @classmethod
    def from_settings(cls, settings):
        from sqlalchemy import engine_from_config
        from sqlalchemy.orm import sessionmaker

        engine = engine_from_config(settings, prefix='sqlalchemy.')
        session = sessionmaker(bind=engine)()

        return cls(session, settings)

    def get_env(self, settings):
        env = self.db.query(M.Environment).filter_by(
            uuid=settings['juju.env.uuid']).first()
        if not env:
            env = M.Environment(
                uuid=settings['juju.env.uuid'],
                name=settings['juju.env.name'],
                provider_type=settings['juju.env.providertype'],
                default_series=settings['juju.env.defaultseries'],
                region=settings['juju.env.region'],
            )
            self.db.add(env)
        return env

    def get_environments(self):
        """Return a query of all Environments.

        """
        return self.db.query(M.Environment)

    def get_unit(self, name):
        """Return Unit identified by ``name``.

        :param name: unit name in the form "unit-pts-0"

        """
        return self.db.query(M.Unit) \
            .filter(M.Unit.environment_id == self.env.id) \
            .filter_by(name=name) \
            .first()

    def set_profile_data(self, key, data):
        """Save profiling data for the unit identified by `key`.

        """
        unit = self.get_unit(key)
        if not unit:
            unit = M.Unit(name=key)
            self.env.units.append(unit)
        unit.data = data

    def get_service(self, name):
        """Return Service named ``name`` in the current environment

        """
        return self.db.query(M.Service) \
            .filter(M.Service.environment_id == self.env.id) \
            .filter_by(name=name) \
            .first()

    def get_services(self):
        """Return all Services in the current environment

        """
        return self.db.query(M.Service) \
            .filter(M.Service.environment_id == self.env.id)

    def get_services_data(self):
        """Return data for all services.

        """
        return {s.name: s.data for s in self.get_services()}

    def get_service_data(self, service):
        """Return data (json) for service.

        """
        svc = self.get_service(service)
        return svc.data if svc else None

    def set_service_data(self, service, data):
        """Save data (json) for service.

        """
        svc = self.get_service(service)
        if not svc:
            svc = M.Service(name=service)
            self.env.services.append(svc)
        svc.data = data

    def get_services_benchmarks(self):
        """Return list of benchmark names, by service.

        Example:

            {
                'pts': ['stream', 'smoke'],
            }

        """
        services = self.get_services_data() or {}
        return {svc: services[svc].get('benchmarks', [])
                for svc in services}

    def is_benchmark_action(self, action):
        """Return True if action is a benchmark (as defined by the charm).

        """
        svc_benchmarks = self.get_services_benchmarks()
        if action.service not in svc_benchmarks:
            return True
        if action.name in svc_benchmarks[action.service]:
            return True
        return False

    def get_benchmarks(self):
        """Return all Actions, grouped by benchmark name.

        """
        benchmarks = {}
        for a in self.get_actions():
            benchmarks.setdefault(a.benchmark_name, []).append(a)
        return benchmarks

    def get_action(self, uuid):
        """Return Action identified by ``uuid``.

        """
        return self.db.query(M.Action).filter_by(uuid=uuid).first()

    def get_actions(self):
        """Return all Actions.

        """
        return self.db.query(M.Action)

    def get_action_data(self, uuid):
        """Return data for an action.

        """
        action = self.get_action(uuid)
        if not action:
            return None
        action.data = action.data or {}
        action.data['graphs'] = {
            g.uuid: g.data for g in action.graphs
        }
        action.data['tags'] = [
            t.name for t in action.tags
        ]
        return action.data
