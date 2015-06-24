from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('api_home', '/api')
    config.add_route('api_benchmarks', '/api/benchmarks')

    config.add_route('home', '/')
    config.add_route('login', '/')

    config.scan()
    return config.make_wsgi_app()
