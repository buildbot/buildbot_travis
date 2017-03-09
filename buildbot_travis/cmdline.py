from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import re
import subprocess

from buildbot_travis import runner

filter_re = re.compile("([A-Z0-9_]+)(!?=)(.*)")


def parse_filter(f):
    res = filter_re.match(f)
    if not res:
        raise ValueError("{} is not a correct filter".format(f))
    return res.group(1), res.group(2), res.group(3)

MASTERCFG = """
from buildbot_travis import TravisConfigurator
c = BuildmasterConfig = {}
TravisConfigurator(BuildmasterConfig, basedir).fromYaml('cfg.yml')
"""


def create_master(args):
    basedir = args.basedir[0]
    subprocess.check_call(["buildbot", "create-master", basedir])
    os.remove(os.path.join(basedir, "master.cfg.sample"))
    with open(os.path.join(basedir, "master.cfg"), 'w') as f:
        f.write(MASTERCFG)
    with open(os.path.join(basedir, "cfg.yml"), 'w') as f:
        f.write("{}")
    subprocess.check_call(["buildbot", "upgrade-master", basedir])
    print("Now you can start your bot with:\n\t% buildbot start", basedir)
    print("and then go to the UI at http://localhost:8010/")

def bbtravis():
    parser = argparse.ArgumentParser(description='Travis commandline')
    subparsers = parser.add_subparsers()
    parser_run = subparsers.add_parser('run', help='run a travis rc')
    parser_run.add_argument('--dryrun', '-n', action='store_true')
    parser_run.add_argument(
        "--num-threads",
        '-j',
        action="store",
        type=int,
        default=1,
        dest="num_threads",
        help="run in parallel")
    parser_run.add_argument(
        '--docker-image',
        '-d',
        help="use docker image to run the bbtravis",
        dest="docker_image")
    parser_run.add_argument(
        '--docker-workdir',
        default="/buildbot",
        help="workdir inside docker container where to run" +
        "(will map current directory, and cd here to run commands)",
        dest="docker_pwd")
    parser_run.add_argument(
        'filters',
        type=parse_filter,
        nargs='*',
        metavar="VAR=foo",
        help="filter matrix (supported operators: '=', '==', '!=')")
    parser_run.set_defaults(func=runner.run)

    parser_create = subparsers.add_parser('create-master', help='create a travis buildbot master')
    parser_create.add_argument(
        'basedir',
        nargs=1,
        help="where to create the master")
    parser_create.set_defaults(func=create_master)



    args = parser.parse_args()
    args.func(args)
