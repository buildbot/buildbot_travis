import argparse
from travisyml import TravisYml, TRAVIS_HOOKS
import subprocess


def loadTravisYml():
    yml = TravisYml()

    with open(".travis.yml") as f:
        yml.parse(f.read())

    return yml


def run(args):
    config = loadTravisYml()

    for env in config.matrix:
        script = "set -v; set -e\n"
        final_env = {}
        for k, v in env.items():
            if k == "env":
                final_env.update(v)
            else:
                final_env[k] = v
        matrix = " ".join(["%s=%s" % (k, v) for k, v in final_env.items()])
        for k, v in final_env.items():
            script += "export %s='%s'\n" % (k, v)

        for k in TRAVIS_HOOKS:
            script += "# " + k + "\n"
            for command in getattr(config, k):
                script += command + "\n"
        print "running matrix", matrix
        subprocess.call(["bash", "-c", script])


def bbtravis():
    parser = argparse.ArgumentParser(description='Travis commandline')
    subparsers = parser.add_subparsers()
    parser_run = subparsers.add_parser('run', help='run a travis rc')
    parser_run.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)
