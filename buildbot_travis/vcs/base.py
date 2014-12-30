# Copyright 2012-2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from buildbot.interfaces import IPlugin
from zope.interface import implements
from buildbot.plugins.db import get_plugins

from twisted.python import log


class IVCSManager(IPlugin):
    """
        Interface for VCS management
        Includes support for ChangeSource and Source step for a vcs type

        VCS registers to the python system via python endpoints in a plugin fashion
    """

    def setupChangeSource(changeSources):
        pass

    def addSourceSteps(factory):
        pass


class VCSBase(object):
    implements(IVCSManager)

    scm_type = None
    subrepos = []
    branch = None
    repository = None

    def __init__(self, **kw):
        # takes all configuration from the yaml
        for k, v in kw.items():
            setattr(self, k, v)

    def addSourceSteps(self, factory):
        self.addRepository(factory, self.name, self.repository, self.branch)
        for subrepo in self.subrepos:
            self.addRepository(
                factory,
                **subrepo
            )


class PollerMixin(object):
    def makePollerDir(self, name):
        # Set up polling for the projects repository
        # Each poller will get its own directory to store state in
        pollerdir = os.path.join(self.vardir, "pollers", name)
        if not os.path.exists(pollerdir):
            log.msg("Creating pollerdir '%s'" % pollerdir)
            os.makedirs(pollerdir)
        return pollerdir


repository_db = {}


def getVCSManagerForRepository(name):
    return repository_db[name]


def addRepository(name, config):
    global repository_db
    vcs_type = config['vcs_type']
    plugins = get_plugins("travis", IVCSManager, load_now=False)
    if vcs_type in plugins.names:
        plugin = plugins.get(vcs_type)
        r = repository_db[name] = plugin(**config)
        return r

    raise KeyError("No VCS manager for %s, got %s" % (vcs_type, plugins.info_all()))
