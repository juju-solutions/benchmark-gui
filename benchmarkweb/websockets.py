import logging

from pyramid.view import view_config
from pyramid.response import Response

from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from socketio.mixins import BroadcastMixin

import gevent
from gevent import Greenlet
from gevent.queue import Queue, Empty

from .api import ActionEnvironment
from .db import DB
from .models import Action

log = logging.getLogger(__name__)

handlers = []


class Actor(gevent.Greenlet):

    def __init__(self):
        self.inbox = Queue()
        Greenlet.__init__(self)

    def receive(self, message):
        """
        Define in your subclass.
        """
        raise NotImplemented()

    def _run(self):
        self.running = True

        while self.running:
            try:
                message = self.inbox.get_nowait()
                self.receive(message)
            except Empty:
                pass
            gevent.sleep(0)


class JujuHandler(Actor):
    def __init__(self, namespace):
        super(JujuHandler, self).__init__()
        self.namespace = namespace
        self.start()

    def receive(self, message):
        self.namespace.emit("event", message)


class DBUpdater(Actor):
    def __init__(self, env, settings, clients):
        super(DBUpdater, self).__init__()
        self.env = env
        self.settings = settings
        self.clients = clients
        self.start()

    def receive(self, message):
        db = DB.from_settings(self.settings)
        try:
            self.update_db(db, message)
            db.session.commit()
            db.session.close()
            # send message to client greenlets
            for c in self.clients:
                c.inbox.put_nowait(message)
        except Exception as e:
            db.session.rollback()
            db.session.close()
            log.exception(e)

    def update_db(self, db, message):
        actions = self.env.actions_list_all()
        for receiver_actions in actions.get('actions', []):
            for action in receiver_actions.get('actions', {}):
                self.update_action(db, action)

    def update_action(self, db, action_data):
        uuid = action_data['action']['tag'][len('action-'):]
        action = db.get_action(uuid=uuid)
        if not action:
            action = Action.from_data(action_data)
            # only persist benchmark Actions
            if db.is_benchmark_action(action):
                db.env.actions.append(action)
        else:
            action.data = action_data
        action.get_profile_data(db)


def juju_api_listener(settings):
    env = ActionEnvironment(settings['juju.api.endpoint'])
    env.login(settings['juju.api.secret'],
              settings['juju.api.user'])

    # store juju env info in global app settings
    for k, v in env.info().items():
        settings['juju.env.{}'.format(k.lower())] = v

    settings['juju.env.region'] = \
        env.get_env_config()['Config'].get('region')

    # start the db-updater greenlet
    db_updater = DBUpdater(env, settings, handlers)

    watch = env.get_watch()
    for msg in watch:
        db_updater.inbox.put_nowait(msg)
        gevent.sleep(0)


class EventsNamespace(BaseNamespace, BroadcastMixin):
    def initialize(self):
        self.juju_handler = JujuHandler(self)
        handlers.append(self.juju_handler)

    def on_event(self, msg):
        self.broadcast_event('event', msg)

    def recv_connect(self):
        self.broadcast_event('user_connect')

    def recv_disconnect(self):
        handlers.remove(self.juju_handler)
        self.broadcast_event('user_disconnect')
        self.disconnect(silent=True)


@view_config(route_name='socket_io')
def socketio_service(request):
    socketio_manage(request.environ,
                    {'/events': EventsNamespace},
                    request=request)

    return Response('')