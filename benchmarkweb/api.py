import jujuclient


def get_service_units(status):
    results = {}
    services = status.get('Services', {})
    for svc_name, svc_data in services.items():
        units = svc_data['Units'] or {}
        sub_to = svc_data['SubordinateTo']
        if not units and sub_to:
            for sub in sub_to:
                for unit_name, unit_data in services[sub]['Units'].items():
                    for sub_name, sub_data in \
                            (unit_data['Subordinates'] or {}).items():
                        if sub_name.startswith(svc_name):
                            units[sub_name] = sub_data
        results[svc_name] = units
    return results


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

        service_units = get_service_units(self.status())
        service_names = [service] if service else service_units.keys()
        units = []

        for name in service_names:
            units += service_units[name].keys()

        for unit in set(units):
            args['Params']['Entities'].append(
                {
                    "Tag": "unit-%s" % unit.replace('/', '-'),
                }
            )

        return self._rpc(args)


class API(object):
    def __init__(self, settings):
        api_endpoint = settings['juju.api.endpoint']
        api_user = settings['juju.api.user']
        api_secret = settings['juju.api.secret']

        try:
            env = ActionEnvironment(api_endpoint)
            env.login(api_secret, user=api_user)
        except jujuclient.EnvError as e:
            raise e

        self.env = env
        self.settings = settings

    @classmethod
    def from_request(cls, request):
        return cls(request.registry.settings)

    def get_status(self):
        return self.env.status()

    def get_annotations(self, services):
        """Return dict of (servicename: annotations) for each servicename
        in `services`.

        """
        if not services:
            return None

        d = {}
        for s in services:
            d[s] = self.env.get_annotation(s, 'service')['Annotations']
        return d

    def get_actions(self, service=None):
        return self.env.actions_list_all(service)

    def get_service_units(self):
        return get_service_units(self.env.status())
