import argparse
import os

from pyramid.paster import bootstrap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ini_file')
    parser.add_argument(
        '-f', '--force',
        help='If tables exist, drop and recreate'
    )
    args = parser.parse_args()

    env = bootstrap(os.path.abspath(args.ini_file))
    request = env['request']

    from benchmarkweb.models import Base
    if args.force:
        Base.metadata.drop_all(request.db.bind)
    Base.metadata.create_all(request.db.bind)


if __name__ == '__main__':
    main()
