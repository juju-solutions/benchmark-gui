import datetime
import difflib
import json
import re

import requests

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPFound,
    HTTPNotFound,
    HTTPServiceUnavailable,
)

from .api import API
from .db import Redis


@view_config(route_name='home', renderer='index.mako')
def root(request):
    # api = API(request)
    # benchmarks = api.get_benchmarks()
    if 'api.juju' in request.POST:
        request.redirect('login')
    return {}

@view_config(route_name='login', renderer='login.mako')
def login(request):
    if not request.POST['api.user']:
        return {}

    if 'api.secret' in request.POST:
        try:
            API(request)
        except:
            return {}
        else:
            return HTTPFound(request.route_url('home'))
    pass

@view_config(route_name='api_home', renderer='json')
def api_root(request):
    api = API(request)
    benchmarks = {}
    results = api.get_benchmarks(request)
    for name, actions in results.items():
        benchmarks[name] = {
            "actions": actions,
            "result_keys": sorted(set(k for a in actions
                                      for k in a.results)),
        }
    return {
        'benchmarks': benchmarks,
        'action_specs': api.get_benchmark_action_specs(),
        'service_units': api.get_service_units(),
    }


@view_config(route_name='api_benchmarks', renderer='json')
def api_benchmarks(request):
    api = API(request)
    return api.get_benchmark_actions() or {}
