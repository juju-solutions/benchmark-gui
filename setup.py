from setuptools import setup

requires = [
    'pyramid',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'gevent-socketio',
    'gevent-websocket',
    'gevent',
    'waitress',
    'jujuclient',
    'redis',
    'requests',
    'nose',
    'coverage',
    'flake8',
    'mock',
    'python-dateutil',
    'humanize',
    'pytz',
    'pyyaml',
    ]

setup(name='benchmarkweb',
      version='0.0.1',
      install_requires=requires,
      url='http://github.com/cloud-benchmarks/benchmark-gui',
      packages=['benchmarkweb'],
      include_package_data=True,
      zip_safe=False,
      entry_points="""\
      [paste.app_factory]
      main = benchmarkweb:main
      """,
      )
