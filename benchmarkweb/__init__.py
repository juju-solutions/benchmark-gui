import gevent
from gevent import monkey
monkey.patch_all()

from pyramid.config import Configurator
from benchmarkweb.websockets import juju_api_listener

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker


def db(request):
    maker = request.registry.dbmaker
    session = maker()

    def cleanup(request):
        if request.exception is not None:
            session.rollback()
        else:
            session.commit()
        session.close()
    request.add_finished_callback(cleanup)

    return session


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    engine = engine_from_config(settings, prefix='sqlalchemy.')
    config.registry.dbmaker = sessionmaker(bind=engine)
    config.add_request_method(db, reify=True)

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('root', '/')
    config.add_route('api_root', '/api')
    config.add_route('api_action_publish', '/api/actions/{action}/publish')
    config.add_route('api_service', '/api/services/{service}')

    config.add_route('socket_io', 'socket.io/*remaining')
    gevent.spawn(juju_api_listener, config.registry.settings)

    config.scan()
    return config.make_wsgi_app()
