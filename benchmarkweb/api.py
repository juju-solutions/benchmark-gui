import datetime
import sys

import jujuclient
import requests
import humanize
import yaml

import dateutil.parser

from .db import Redis

# Doesn't get configuration...
def make_bundle(status_json):
    def parse_hardware(hardware):
        # Blacklist availability-zone?
        return hardware.split(' ')

    status = json.loads(status_json)
    bundle = {'services': {}, 'relations': []}
    for service, data in status['Services'].iteritems():
        bundle['services'][service] = {'charm': data['Charm']}
        if data['Units']:
            unit = data['Units'].keys()[0]
            unit_data = data['Units'][unit]
            hardware = status['Machines'][unit_data['Machine']]['Hardware']
            bundle['services'][service]['constraints'] = parse_hardware(hardware)
            bundle['services'][service]['num_units'] = len(data['Units'].keys())

    for r in status['Relations']:
        if ' ' in r['Key']:
            bundle['relations'].append(r['Key'].split(' '))
    return bundle


def make_submission(action, bundle, environment):
    output = {
        'version': '1.0',
        'action': action,
        'bundle': bundle,
        'environment': environment
    }

    pass


def get_environment_details(env):
    pass


def trim_bundle(d, svc):
    rels = d['relations']
    svcs = d['services']

    def get_descendants(svc, rels):
        found = False

        if svc in ('benchmark-gui'):
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


class ActionEnvironment(jujuclient.Environment):
    def actions_available(self, service=None):
        args = {
            "Type": 'Action',
            "Request": 'ServicesCharmActions',
            "Params": {
                "Entities": []
            }
        }

        services = self.status().get('Services', {})
        service_names = [service] if service else services
        for name in service_names:
            args['Params']['Entities'].append(
                {
                    "Tag": 'service-' + name
                }
            )

        return self._rpc(args)

    def actions_list_all(self, service=None):
        args = {
            "Type": 'Action',
            "Request": 'ListAll',
            "Params": {
                "Entities": []
            }
        }

        services = self.status().get('Services', {})
        service_names = [service] if service else services
        for name in service_names:
            for unit in services[name]['Units'] or []:
                args['Params']['Entities'].append(
                    {
                        "Tag": "unit-%s" % unit.replace('/', '-'),
                    }
                )

        return self._rpc(args)

    def actions_enqueue(self, action, receivers, params=None):
        args = {
            "Type": "Action",
            "Request": "Enqueue",
            "Params": {
                "Actions": []
            }
        }

        for receiver in receivers:
            args['Params']['Actions'].append({
                "Receiver": receiver,
                "Name": action,
                "Parameters": params or {},
            })

        return self._rpc(args)

    def actions_cancel(self, uuid):
        return self._rpc({
            'Type': 'Action',
            'Request': 'Cancel',
            "Params": {
                "Entities": [{'Tag': 'action-' + uuid}]
            }
        })


def get_api_endpoint():
    import os
    if 'API_ENDPOINT' in os.environ:
        return os.environ['API_ENDPOINT']

    if os.path.exists('/etc/benchmark-gui.conf'):
        with open('/etc/benchmark-gui.conf') as f:
            cfg = yaml.safe_load(f.read())

        if 'api-endpoint' in cfg:
            return cfg['api-endpoint']

    return None


class API(object):
    def __init__(self, request):
        api_endpoint = get_api_endpoint()
        api_user = request.POST['juju.api.user']
        api_secret = request.POST['juju.api.secret']

        try:
            env = ActionEnvironment(api_endpoint)
            env.login(api_secret, user=api_user)
        except jujuclient.EnvError as e:
            # _exit("Couldn't connect to Juju API server: {}".format(
            #    e.message))
            raise e

        self.env = env
        self.request = request

    def get_status(self):
        return self.env.status()

    def get_actions(self, service=None):
        return self.env.actions_list_all(service)

    def get_action(self, uuid):
        results = self.get_actions()
        if not results:
            return None

        uuid = 'action-' + uuid
        for receiver_actions in results.get('actions', []):
            for action in receiver_actions.get('actions', {}):
                if uuid == action['action']['tag']:
                    return Action(action)

    def get_benchmark_actions(self, service=None):
        actions = self.env.actions_list_all(service)
        if not actions:
            return actions

        service_benchmarks = Redis(self.request).get_services_benchmarks()
        benchmark_actions = {'actions': []}
        for receiver_actions in actions.get('actions', []):
            receiver = receiver_actions['receiver']
            service = '-'.join(receiver.split('-')[1:-1])
            if service not in service_benchmarks:
                # We don't have a list of benchmark names for this
                # service, so we don't know which of its actions are
                # benchmarks. Not knowing for sure, we keep them all.
                benchmark_actions['actions'].append(receiver_actions)
                continue
            keeper_actions = []
            for action in receiver_actions.get('actions', {}):
                if action['action']['name'] not in service_benchmarks[service]:
                    continue
                keeper_actions.append(action)
            if not keeper_actions:
                continue
            receiver_actions['actions'] = keeper_actions
            benchmark_actions['actions'].append(receiver_actions)

        if not benchmark_actions['actions']:
            return None
        return benchmark_actions

    def get_benchmarks(self, request=None):
        benchmarks = {}

        actions = self.get_benchmark_actions()
        if not actions:
            return benchmarks

        for receiver_actions in actions.get('actions', []):
            for action in receiver_actions.get('actions', {}):
                a = Action(action)
                if request:
                    a.get_tags(request)
                    a.get_profile_data(request)
                benchmarks.setdefault(a.benchmark_name, []).append(a)
        return benchmarks

    def get_service_units(self):
        results = {}

        services = self.env.status().get('Services', {})
        for svc_name, svc_data in services.items():
            results[svc_name] = svc_data['Units']
        return results

    def get_action_specs(self):
        results = self.env.actions_available()
        return _parse_action_specs(results)

    def get_benchmark_action_specs(self):
        action_specs = self.get_action_specs()
        if not action_specs:
            return action_specs

        service_benchmarks = Redis(self.request).get_services_benchmarks()
        for service in action_specs.keys()[:]:
            if service not in service_benchmarks:
                continue
            for spec_name in action_specs[service].keys()[:]:
                if spec_name not in service_benchmarks[service]:
                    action_specs[service].pop(spec_name)
            if not action_specs[service]:
                action_specs.pop(service)
        return action_specs

    def enqueue_action(self, action, receivers, params):
        result = self.env.actions_enqueue(action, receivers, params)
        return Action(result['results'][0])


def _parse_action_specs(api_results):
    results = {}

    r = api_results['results']
    for service in r:
        servicetag = service['servicetag']
        service_name = servicetag[8:]  # remove 'service-' prefix
        specs = {}
        if service['actions']['ActionSpecs']:
            for spec_name, spec_def in service['actions']['ActionSpecs'].items():
                specs[spec_name] = ActionSpec(spec_name, spec_def)
        results[service_name] = specs
    return results


def _parse_action_properties(action_properties_dict):
    results = {}

    d = action_properties_dict
    for prop_name, prop_def in d.items():
        results[prop_name] = ActionProperty(prop_name, prop_def)
    return results


def _get_graph_url(request, action, format_=None, target=None):
    graphite_url = request.registry.settings['graphite.url']
    graphite_format = format_ or request.registry.settings['graphite.format']
    #target = target or '{}.*.*.*'.format(action.receiver)
    target = '*.*.*.*'

    def _format_date(d):
        if not d:
            return d

        return d.astimezone(dateutil.tz.tzutc()).strftime('%H:%M_%Y%m%d')

    start = _format_date(action.start) or '-5min'
    stop = _format_date(action.stop)

    tpl = '{}/render?height=340&width=420&target={}&format={}&bgcolor=00000000'
    url = tpl.format(
        graphite_url, target, graphite_format)

    if start:
        url += '&from={}'.format(start)
    if stop:
        url += '&until={}'.format(stop)

    return url


class Dict(dict):
    def __getattr__(self, name):
        return self[name]


class Graph(Dict):
    pass


class Action(dict):
    def __init__(self, *args, **kw):
        super(Action, self).__init__(*args, **kw)
        self['uuid'] = self.uuid
        self['unit'] = self.unit
        self['duration'] = str(self.duration or '')
        self['service'] = self.service
        self['name'] = self.name
        self['started'] = self.started

    def get_bundle_data(self, request):
        from .db import Redis
        p = Redis(request).get_profile_data(
            self.receiver, self.uuid, self.start, self.stop)
        p = p[0] if p else None
        try:
            b = make_bundle(p.get('status'))
            b = yaml.load(b).values()[0]
            b = trim_bundle(b, self.service)
            self['bundle'] = yaml.safe_dump(b, default_flow_style=False)
        except Exception as e:
            sys.stderr.write(str(e) + '\n')
        return self['bundle']

    def get_graphs(self, request):
        from .db import Redis
        action = Redis(request).get_action(self.uuid) or {}
        self['graphs'] = action.get('graphs', {})
        return self['graphs']

    def get_tags(self, request):
        from .db import Redis
        action = Redis(request).get_action(self.uuid) or {}
        self['tags'] = action.get('tags', [])
        return self['tags']

    def get_metrics(self, request, format_='json'):
        url = _get_graph_url(request, self, format_=format_)
        return requests.get(url)

    @property
    def benchmark_name(self):
        return '{}:{}'.format(self.service, self.name)

    @property
    def service(self):
        _, service, unit = self['action']['receiver'].split('-')
        return service

    @property
    def name(self):
        return self['action']['name']

    @property
    def status(self):
        return self['status']

    @property
    def start(self):
        return self._date('started')

    @property
    def started(self):
        start = self.start
        if not start and self.status in ['pending', 'running', 'canceling']:
            start = datetime.datetime.utcnow()
        return start.strftime("%Y-%m-%dT%H:%M:%SZ") if start else None

    @property
    def stop(self):
        if not self.start:
            return None

        if not self._date('completed') or self._date('completed') < self.start:
            return None

        return self._date('completed')

    def _date(self, key):
        date = self.get(key)
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

        t = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())
        return humanize.naturaltime(t - self.start)

    @property
    def human_stop(self):
        if not self.stop:
            return None

        t = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())
        return humanize.naturaltime(t - self.stop)

    @property
    def tag(self):
        return self['action']['tag']

    @property
    def uuid(self):
        return self.tag[len('action-'):]

    @property
    def receiver(self):
        return self['action']['receiver']

    @property
    def parameters(self):
        return self['action'].get('parameters', {})

    @property
    def unit(self):
        return self.receiver[len('unit-'):].replace('-', '/')

    @property
    def results(self):
        return self.get('output', {}).get('results', {})


class ActionSpec(Dict):
    def __init__(self, name, data_dict):
        params = data_dict['Params']
        super(ActionSpec, self).__init__(
            name=name,
            title=params['title'],
            description=params['description'],
            properties=_parse_action_properties(params['properties'])
        )


class ActionProperty(Dict):
    types = {
        'string': str,
        'integer': int,
        'boolean': bool,
        'number': float,
    }
    type_checks = {
        basestring: 'string',
        int: 'integer',
        bool: 'boolean',
        float: 'number',
    }

    def __init__(self, name, data_dict):
        super(ActionProperty, self).__init__(
            name=name,
            description=data_dict.get('description', ''),
            default=data_dict.get('default', ''),
            type=data_dict.get(
                'type', self._infer_type(data_dict.get('default'))),
        )

    def _infer_type(self, default):
        if default is None:
            return 'string'
        for _type in self.type_checks:
            if isinstance(default, _type):
                return self.type_checks[_type]
        return 'string'

    def to_python(self, value):
        f = self.types.get(self.type)
        return f(value) if f else value
