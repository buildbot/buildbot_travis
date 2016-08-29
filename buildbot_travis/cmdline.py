import argparse
import os
import subprocess

from travisyml import TRAVIS_HOOKS, TravisYml


def loadTravisYml():
    yml = TravisYml()
    for filename in [".bbtravis.yml", ".travis.yml"]:
        if os.path.exists(filename):
            with open(filename) as f:
                yml.parse(f.read())
            break
    return yml


def run(args):
    config = loadTravisYml()

    for env in config.matrix:
        script = "set -v; set -e\n"
        final_env = {"TRAVIS_PULL_REQUEST": 1}
        for k, v in env.items():
            if k == "env":
                final_env.update(v)
            else:
                final_env[k] = v
        matrix = " ".join(["%s=%s" % (k, v) for k, v in final_env.items()])
        for k, v in final_env.items():
            script += "export %s='%s'\n" % (k, v)


        print "running matrix", matrix
        print "========================"
        for k in TRAVIS_HOOKS:
            print "running hook", k
            print "--------------------"
            for command in getattr(config, k):
                title = None
                condition = None
                if isinstance(command, dict):
                    title = command.get("title")
                    condition = command.get("condition")
                    command = command['cmd']
                if title:
                    print "title:", title
                if condition and not eval(condition, final_env):
                    print "not run because of", condition
                    continue
                print command
                if not args.dryrun:
                    subprocess.checkcall(["bash", "-c", script + "\n" + command])


def bbtravis():
    parser = argparse.ArgumentParser(description='Travis commandline')
    subparsers = parser.add_subparsers()
    parser_run = subparsers.add_parser('run', help='run a travis rc')
    parser_run.add_argument('--dryrun', '-n', action='store_true')
    parser_run.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)
