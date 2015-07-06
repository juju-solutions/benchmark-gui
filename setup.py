from setuptools import setup

requires = [
    'alembic',
    'coverage',
    'flake8',
    'gevent-socketio',
    'gevent-websocket',
    'gevent',
    'humanize',
    'jujuclient',
    'mock',
    'nose',
    'psycopg2',
    'pyramid',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'python-dateutil',
    'pyyaml',
    'pytz',
    'requests',
    'sqlalchemy',
    'waitress',
    ]

setup(name='benchmarkweb',
      version='0.0.0',
      install_requires=requires,
      url='http://github.com/juju-solutions/benchmark-web',
      packages=['benchmarkweb'],
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [paste.app_factory]
      main = benchmarkweb:main
      [console_scripts]
      initialize_db = benchmarkweb.scripts.initialize_db:main
      """,
      )
