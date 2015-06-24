import json
import unittest
from mock import patch

from pyramid import registry
from pyramid import testing


def _get_test_request():
    request = testing.DummyRequest()
    request.registry = registry.Registry()
    request.registry.settings = {
        'graphite.url': 'http://localhost:9000',
        'graphite.format': 'png',
        'juju.api.endpoint': '',
        'juju.api.user': '',
        'juju.api.secret': '',
    }
    return request


class MockActionEnvironment(object):
    def status(self):
        return {}

    def actions_list_all(self, service=None):
        return {
            "actions": [
                {
                    "actions": [
                        {
                            "action": {
                                "name": "smoke",
                                "receiver": "unit-pts-0",
                                "tag": "action-f3c00159-08b4-42c2-8892-0d0b71f78575"
                            },
                            "output": {
                                "meta": {
                                    "start": "2015-01-13T17:00:27Z",
                                    "stop": "2015-01-13T17:00:43Z"
                                }
                            },
                            "status": "completed"
                        }
                    ],
                    "receiver": "unit-pts-0"
                }
            ]
        }
        # "graph": "http://localhost:9000/render?target=unit-pts-0.*.*&from=17:00_20150113&until=17:00_20150113&format=png",

    def actions_available(self, service=None):
        return {
            "results": [
                {
                    "servicetag": "service-pts",
                    "actions": {
                        "ActionSpecs": {
                            "smoke": {
                                "Params": {
                                    "title": "smoke",
                                    "type": "object",
                                    "description": "Smoke test, tests that complete quickly.",
                                    "properties": {
                                        "tests": {
                                            "default": "pts/phpbench pts/cachebench pts/stream",
                                            "type": "string",
                                            "description": "Memory centric stress tests"
                                        }
                                    }
                                },
                                "Description": "Smoke test, tests that complete quickly."
                            },
                        }
                    }
                }
            ]
        }


class MockRedis(object):
    data = {
        "unit-pts-0":
        {
            "foo": "bar"
        }
    }

    def get(self, s):
        item = self.data.get(s)
        return json.dumps(item) if item else None

    def set(self, key, val):
        self.data[key] = val

    def get_profile_data(self, key, action=None, start=None, stop=None):
        return [self.data.get(key)]


class ViewTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        import benchmarkweb.views

        self.config = testing.setUp()
        patch.object(
            benchmarkweb.views, 'Redis', lambda req: MockRedis()).start()
        mock_env = patch('benchmarkweb.api.ActionEnvironment').start()

        mock_env.return_value.actions_available.side_effect = \
            MockActionEnvironment().actions_available
        mock_env.return_value.actions_list_all.side_effect = \
            MockActionEnvironment().actions_list_all
        mock_env.return_value.status.side_effect = \
            MockActionEnvironment().status

        self.request = _get_test_request()
        self.api = benchmarkweb.views.API(self.request)

    def tearDown(self):
        patch.stopall()
        testing.tearDown()

    def test_actions(self):
        from .views import actions
        request = self.request
        d = actions(request)
        self.assertEqual(d['actions'], self.api.get_actions())

    def test_action(self):
        from .views import action
        uuid = 'f3c00159-08b4-42c2-8892-0d0b71f78575'
        request = self.request
        request.matchdict['action'] = uuid
        d = action(request)
        action = self.api.get_action(uuid)
        self.assertEqual(d['action'], action)

    def test_action_create(self):
        from views import action_create
        import webob
        request = self.request
        request.route_url = lambda route_name: '/actions'
        d = request.params = webob.multidict.MultiDict()
        d['action'] = 'smoke'
        d['service'] = 'pts'
        d['receivers'] = 'unit-pts-0'
        d['prop-tests'] = 'pts/stream'
        action_create(request)
        self.api.env.actions_enqueue.assert_called_once_with(
            'smoke', ['unit-pts-0'], {'tests': 'pts/stream'}
        )

    def test_api_actions(self):
        from .views import api_actions
        request = self.request
        d = api_actions(request)
        self.assertEqual(d, self.api.get_actions())

    def test_api_action(self):
        from .views import api_action
        uuid = 'f3c00159-08b4-42c2-8892-0d0b71f78575'
        request = self.request
        request.matchdict['action'] = uuid
        d = api_action(request)
        action = self.api.get_action(uuid)
        self.assertEqual(d, action)

    def test_unit_get(self):
        from views import unit
        request = self.request
        request.matchdict['service'] = 'pts'
        request.matchdict['unit'] = '0'
        d = unit(request)
        self.assertEqual(d['unit'], MockRedis().get_profile_data('unit-pts-0'))

    def test_api_unit_get(self):
        from views import api_unit_get
        request = self.request
        request.matchdict['service'] = 'pts'
        request.matchdict['unit'] = '0'
        d = api_unit_get(request)
        self.assertEqual(d, MockRedis().get_profile_data('unit-pts-0'))

    def test_api_unit_post(self):
        from views import api_unit_post
        request = self.request
        request.matchdict['service'] = 'pts'
        request.matchdict['unit'] = '0'
        request.json_body = {"foo": "baz"}
        api_unit_post(request)
        self.assertEqual(
            request.json_body,
            json.loads(MockRedis.data['unit-pts-0'])[-1]['data'])
