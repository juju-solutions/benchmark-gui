import datetime
import json
import textwrap

import pkg_resources
import requests

from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotAcceptable,
    HTTPNotFound,
)

from .api import API
from .db import DB

VERSION = pkg_resources.get_distribution('benchmarkweb').version


@view_config(route_name='root', renderer='index.mako')
def root(request):
    """ Base view to load our single-page-app template.

    GET /

    """
    # Make sure we can connect to juju api and display error if not
    s = request.registry.settings
    try:
        api = API(None, s)  # noqa
    except Exception as e:
        def mask(s):
            if not s:
                return s
            if len(s) < 5:
                return '*' * len(s)
            return '*' * (len(s) - 4) + s[-4:]

        secret = mask(s.get('juju.api.secret'))
        request.override_renderer = 'error.mako'
        return {
            'title': 'Error Connecting to Juju API',
            'msg': textwrap.dedent("""\
                Error: {}

                Are the API credentials correct?

                juju.api.endpoint: {}
                juju.api.user: {}
                juju.api.secret: {}""".format(
            e.message, s.get('juju.api.endpoint'),
            s.get('juju.api.user'), secret)),
        }

    return {'version': VERSION}


@view_config(route_name='api_root', renderer='json')
def api_root(request):
    """
    GET /api

    """
    db = DB.from_request(request)

    benchmarks = {}
    results = db.get_benchmarks()
    for name, actions in results.items():
        benchmarks[name] = {
            "actions": [a.to_dict() for a in actions],
            "result_keys": sorted(set(k for a in actions
                                      for k in a.results)),
        }
    return {
        'benchmarks': benchmarks,
        'settings': {
            'can_publish': bool(request.registry.settings.get('publish.url')),
        },
        'environment': db.env.to_dict(shallow=True),
        'environment_count': db.get_environments().count(),
        'version': VERSION,
    }


@view_config(route_name='api_unit', renderer='json', request_method='GET')
def api_unit_get(request):
    service = request.matchdict['service']
    unit = request.matchdict['unit']
    action = request.params.get('action')
    key = 'unit-{}-{}'.format(service, unit)

    db = DB.from_request(request)
    result = db.get_profile_data(key, action=action)
    return result or HTTPNotFound()


@view_config(route_name='api_unit', request_method='POST')
def api_unit_post(request):
    service = request.matchdict['service']
    unit = request.matchdict['unit']
    key = 'unit-{}-{}'.format(service, unit)
    data = request.json_body

    api = API.from_request(request)
    db = DB.from_request(request)

    status = api.get_status()
    services = status.get('Services', []).keys()
    annotations = api.get_annotations(services)

    existing = db.get_profile_data(key) or []
    existing.append({
        "data": data,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": request.params.get('action'),
        "status": status,
        "annotations": annotations,
    })

    db.set_profile_data(key, existing)
    return HTTPFound()


@view_config(route_name='api_service', renderer='json', request_method='GET')
def api_service_get(request):
    service = request.matchdict['service']

    r = DB.from_request(request)
    result = r.get_service_data(service)
    return result or HTTPNotFound()


@view_config(route_name='api_service', request_method='POST')
def api_service_post(request):
    service = request.matchdict['service']
    data = request.json_body

    r = DB.from_request(request)
    r.set_service_data(service, data)
    return HTTPFound()


@view_config(route_name='api_action_publish', request_method='POST',
             renderer='json')
def api_action_publish(request):
    """Submit benchmark data to cloud-benchmarks.org

    POST /api/actions/:action/publish

    """
    uuid = request.matchdict['action']
    publish_url = request.registry.settings.get('publish.url')
    if not publish_url:
        return HTTPNotAcceptable('Publish url not defined')

    db = DB.from_request(request)
    action = db.get_action(uuid)
    if not action:
        return HTTPNotFound('No such action')
    if not action.stop:
        return HTTPNotAcceptable('Action is still running')

    data = action.to_submission()
    if not data:
        return HTTPNotAcceptable('No bundle data for action')

    r = requests.post(publish_url, data=json.dumps(data))
    if r.status_code != requests.codes.ok:
        request.response.status = r.status_code
        response_body = {}
        try:
            response_body = r.json()
        except ValueError:
            pass
        return response_body

    return {}
