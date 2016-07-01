import os

from twisted.application import service
from buildbot.master import BuildMaster

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

