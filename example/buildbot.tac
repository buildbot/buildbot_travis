import os

from twisted.application import service
from buildbot.master import BuildMaster
from buildslave.bot import BuildSlave


# setup master
basedir = os.path.abspath(os.path.dirname(__file__))
configfile = 'master.cfg'

# Default umask for server
umask = None

# note: this line is matched against to check that this is a buildmaster
# directory; do not edit it.
application = service.Application('buildmaster')
import sys

from twisted.python.log import ILogObserver, FileLogObserver

application.setComponent(ILogObserver, FileLogObserver(sys.stdout).emit)

m = BuildMaster(basedir, configfile, umask)
m.setServiceParent(application)

# and slave on the same process!

buildmaster_host = 'localhost'
port = 19989
slavename = 'slave'
passwd = 'pass'
keepalive = 600
usepty = 0
umask = None
maxdelay = 300
allow_shutdown = None
slavedir = os.path.join(basedir, "slave")
if not os.path.exists(slavedir):
    os.mkdir(slavedir)

s = BuildSlave(buildmaster_host, port, slavename, passwd, slavedir,
               keepalive, usepty, umask=umask, maxdelay=maxdelay,
               allow_shutdown=allow_shutdown)
s.setServiceParent(application)
