#! /usr/bin/env python

import os, sys, optparse, subprocess
from yaml import load

if not os.path.exists(".travis.yml"):
    print "Cannot find .travis.yml"
    sys.exit(1)

config = load(open(".travis.yml"))

if not "language" in config:
    print "Please set the language in your .travis.yml!"
    sys.exit(1)

if config["language"] != "python":
    print "Only python is really supported so far.."
    sys.exit(1)


p = optparse.OptionParser()
opts, args = p.parse_args()

if len(args) != 1:
    print "Wrong number of args"
    sys.exit(1)

step = args[0].replace("-", "_")

commands = config.get(step, [])
if isinstance(commands, basestring):
    commands = [commnads]

if not commands:
    if step == "install":
        if os.path.exists("buildout.cfg"):
            if os.path.exists("bootstrap.py"):
                commands.append("python bootstrap.py")
            PATH = ["./bin"] + os.environ["PATH"].split(":")
            for p in PATH:
                cmd = os.path.join(PATH, "buildout")
                if os.path.exists(cmd):
                    commands.append(cmd)
                    break
    elif step == "script":
        if os.path.exists("bin/test"):
            commands.append("./bin/test")

if not commands:
    print "==> Executed 0 commands"
    sys.exit(0)

count = 0
for cmd in commands:
    count += 1

    print "==> ", cmd
    sys.stdout.flush()
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print str(e) + "\n\n"
        print "==> Executed %d commands" % count
        sys.exit(1)

    print "\n\n"
    sys.stdout.flush()

print "==> Executed %d commands" % count

