import datetime
import json
import uuid

import pytz
import redis


class Redis(redis.StrictRedis):
    def __init__(self, request):
        super(Redis, self).__init__(
            host=request.registry.settings['redis.host'],
            port=request.registry.settings['redis.port'],
            db=int(request.registry.settings['redis.db']),
        )

    def get_profile_data(self, key, action=None, start=None, stop=None):
        """Return saved profiling data for the unit identified by `key`.

        :param key: unit name in the form "unit-pts-0"

        Optionally filter on `action` (uuid).
        Optionally filter on `start` <= timestamp >= `stop`.

        """
        result = self.get(key)
        if not result:
            return None

        result = json.loads(result)
        if not isinstance(result, list):
            result = [result]

        if not (action or start or stop):
            return result

        def match(d):
            if action and d.get('action') != action:
                return False
            ts = d.get('timestamp')
            if ts:
                ts = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                ts = pytz.utc.localize(ts)
            if (start and ts) and (ts < start):
                return False
            if (stop and ts) and (ts > stop):
                return False
            return True

        return [d for d in result if match(d)]

    def set_profile_data(self, key, data):
        """Save profiling data for the unit identified by `key`.

        """
        self.set(key, json.dumps(data))

    def get_services_data(self):
        """Return data for all services.

        """
        result = self.get('services')
        return json.loads(result) if result else None

    def get_service_data(self, service):
        """Return data (json) for service.

        """
        result = self.get_services_data()
        return result.get(service) if result else None

    def set_service_data(self, service, data):
        """Save data (json) for service.

        """
        def update(pipe):
            d = self.get_services_data() or {}
            d[service] = data
            pipe.multi()
            pipe.set('services', json.dumps(d))

        self.transaction(update, 'services')

    def get_services_benchmarks(self):
        """Return list of benchmark names, by service.

        Example:

            {
                'pts': ['stream', 'smoke'],
            }

        """
        services = self.get_services_data() or {}
        return {svc: services[svc].get('benchmarks', []) for svc in services}

    def get_action(self, uuid):
        """Return data for an action.

        """
        result = self.get(uuid)
        return json.loads(result) if result else None

    def update_action_tags(self, action_uuid, tags):
        """Update the list of tags associated with an action.

        """

        def update_action(pipe):
            action = self.get_action(action_uuid) or {}
            action['tags'] = tags
            pipe.multi()
            pipe.set(action_uuid, json.dumps(action))

        self.transaction(update_action, action_uuid)

    def insert_action_graph(self, action_uuid, datapoints, label):
        """Save a new graph and return its uuid.

        """
        graph_uuid = uuid.uuid4().hex
        graph = {
            'datapoints': datapoints,
            'label': label,
        }

        def update(pipe):
            action = self.get_action(action_uuid) or {}
            action.setdefault('graphs', {})[graph_uuid] = graph
            pipe.multi()
            pipe.set(action_uuid, json.dumps(action))

        self.transaction(update, action_uuid)
        return graph_uuid

    def delete_action_graph(self, action_uuid, graph_uuid):
        """Delete a graph.

        """
        def update(pipe):
            action = self.get_action(action_uuid) or {}
            del action['graphs'][graph_uuid]
            pipe.multi()
            pipe.set(action_uuid, json.dumps(action))

        self.transaction(update, action_uuid)

    def get_comparison(self, uuid):
        """Return data for an action comparison.

        """
        result = self.get(uuid)
        return json.loads(result) if result else None

    def insert_comparison_graph(self, comparison_id, datapoints, label):
        """Save a new graph and return its uuid.

        """
        graph_uuid = uuid.uuid4().hex
        graph = {
            'datapoints': datapoints,
            'label': label,
        }

        def update(pipe):
            comp = self.get_comparison(comparison_id) or {}
            comp.setdefault('graphs', {})[graph_uuid] = graph
            pipe.multi()
            pipe.set(comparison_id, json.dumps(comp))

        self.transaction(update, comparison_id)
        return graph_uuid

    def delete_comparison_graph(self, comparison_id, graph_uuid):
        """Delete a graph.

        """
        def update(pipe):
            comp = self.get_comparison(comparison_id) or {}
            del comp['graphs'][graph_uuid]
            pipe.multi()
            pipe.set(comparison_id, json.dumps(comp))

        self.transaction(update, comparison_id)
