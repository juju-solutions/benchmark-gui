#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import re
import shlex
import subprocess
import sys
import yaml

INVALID_HW_CONSTRAINTS = ('availability-zone',)


def run(cmd):
    return subprocess.check_output(
        shlex.split(cmd), stderr=subprocess.PIPE)


def get_environment():
    environment = os.environ.get("JUJU_ENV")
    if not environment:
        try:
            environment = run("juju env").strip()
        except:
            return None
    return environment


class Service(object):
    def __init__(self, name, status, machines, api, options):
        self.name = name
        self.status = status
        self.machines = machines
        self.api = api
        self.options = options
        self.service = api.get_service(name)
        self.annotations = api.get_annotation(name, 'service')['Annotations']

        self.constraints = self._get_constraints()
        self.config = self._get_config()
        self.relations = list(self._get_relations())

    def get_bundle_format(self):
        d = {
            'num_units': self.units,
            'charm': self.charm,
        }

        if self.annotations:
            d['annotations'] = self.annotations

        if self.constraints:
            d['constraints'] = self.constraints

        if len(self.config):
            d['options'] = self.config

        if self.options.include_placement and self.placement:
            d['to'] = self.placement

        return d

    def _get_constraints(self):
        d = {}
        d.update(self.api.get_env_constraints()['Constraints'])
        d.update(self.service['Constraints'] or {})

        if not d:
            d.update(self._get_hw_constraints())

        return d

    def _get_hw_constraints(self):
        if not self.status['Units']:
            return {}

        for unit, data in self.status['Units'].items():
            hardware = self.machines[data['Machine']]['Hardware']
            constraints = dict(c.split('=') for c in hardware.split())
            for k in INVALID_HW_CONSTRAINTS:
                constraints.pop(k, None)
            return constraints

    def _get_config(self):
        config = self.service['Config'] or {}

        result = {}
        for k, v in config.items():
            if v.get('default') and not self.options.include_defaults:
                continue
            if 'value' in v:
                result[k] = v['value']
        return result

    def _get_relations(self):
        relations = self.status.get('Relations') or {}
        for name, items in relations.items():
            for item in items:
                if self.name != item:
                    yield sorted([self.name, item])

    @property
    def units(self):
        if 'Units' in self.status:
            return len(self.status.get("Units") or [])
        return 1

    @property
    def charm(self):
        def r(m):
            return m.groups()[0]

        format_ = self.options.location_format

        if self.options.include_charm_versions:
            charm = self.status.get('Charm')
        else:
            charm = re.sub("(.*)(\-[0-9]+)", r,
                           self.status.get('Charm'))

        if format_ == "cs" and charm.startswith("local"):
            return charm.replace("local", "cs")
        elif format_ == "local" and charm.startswith("cs"):
            return charm.replace("cs", "local")
        else:
            return charm

    @property
    def placement(self):
        units = self.status.get('Units')
        if units:
            if len(units) > 1:
                return map(lambda x: x.get('Machine'), units.values())
            else:
                return units[units.keys()[0]].get('Machine')
        return None


class Environment(object):
    def __init__(self, api, options):
        self.api = api
        self.options = options
        self.status = api.status()

    @property
    def services(self):
        for name, data in self.status.get('Services').items():
            yield Service(
                name, data, self.status['Machines'], self.api, self.options
            )

    def get_bundle(self, name=None, as_yaml=True):
        services, relations = {}, []
        bundle_name = name or self.api.info()['Name']

        for service in self.services:
            for relation in service.relations:
                if relation not in relations:
                    relations.append(relation)

            services[service.name] = service.get_bundle_format()

        bundle = {
            bundle_name: {
                'services': services,
                'relations': relations,
            }
        }

        if as_yaml:
            return yaml.safe_dump(bundle, default_flow_style=False)
        return bundle


def parse_options():
    parser = argparse.ArgumentParser(
        description='Convert your current juju environment status\
            into a YAML suitable for being used on juju-deployer')

    parser.add_argument("-e", "--environment",
                        help='Juju environment to convert',
                        type=str,
                        default="",
                        metavar='environment')

    parser.add_argument("-o", "--output",
                        help='File to save the yaml bundle (default: stdout)',
                        type=str,
                        default="",
                        metavar='output')

    parser.add_argument('--include-defaults',
                        action='store_true',
                        default=False,
                        dest='include_defaults',
                        help=('Include configuration values even if they are'
                              ' the default ones'))

    parser.add_argument('--include-charm-versions',
                        action='store_true',
                        default=False,
                        dest='include_charm_versions',
                        help=('Include the exact deployed charm version'))

    parser.add_argument('--include-placement',
                        action='store_true',
                        default=False,
                        dest='include_placement',
                        help=('Include service machine/container placement'))

    parser.add_argument('--charm-location-format',
                        metavar='format',
                        default="cs",
                        type=str,
                        dest='location_format',
                        help=('Replace charm location to format \
                        (options: local,cs)'))

    args = parser.parse_args()

    args.environment = args.environment or get_environment()
    if not args.environment:
        parser.error("Couldn't detect juju env, please specify with -e")

    return args


def get_default_options():
    class O(object):
        pass

    options = O()
    options.include_defaults = False
    options.include_charm_versions = True
    options.include_placement = False
    options.location_format = 'cs'
    return options


def get_bundle(api, name=None, as_yaml=True, options=None):
    options = options or get_default_options()
    env = Environment(api, options)
    return env.get_bundle(name=name, as_yaml=as_yaml)


def get_api(env_name):
    import jujuclient
    return jujuclient.Environment.connect(env_name)


def main():
    options = parse_options()
    api = get_api(options.environment)
    bundle = get_bundle(api, options=options)
    if options.output:
        with open(options.output, 'w+') as f:
            f.write(bundle)
    else:
        sys.stdout.write(bundle)


if __name__ == "__main__":
    main()
