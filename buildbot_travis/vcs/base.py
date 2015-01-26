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
from buildbot.plugins import schedulers
from buildbot.plugins import util
from buildbot.schedulers.forcesched import CodebaseParameter

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
    supportsTry = False  # supports try branches, and change filter
    scm_type = None
    subrepos = []
    branch = None
    repository = None

    def __init__(self, **kw):
        # takes all configuration from the yaml
        for k, v in kw.items():
            setattr(self, k, v)

    def addRepository(self, factory, name, repository, branch):
        raise NotImplemented()

    def addSourceSteps(self, factory):
        self.addRepository(factory, self.name, self.repository, self.branch)
        for subrepo in self.subrepos:
            self.addRepository(
                factory,
                **subrepo
            )
    def createCodebaseParams(self, codebases):
        codebases_params = []
        for name, codebase in codebases.items():
            codebases_params.append(CodebaseParameter(name,
                                                      project="",
                                                      repository=codebase['repository'],
                                                      branch=codebase.get('branch'),
                                                      revision=None,
                                                      ))
        return codebases_params

    def setupSchedulers(self, _schedulers, spawner_name, try_name, importantManager, codebases):
        filt = dict(repository=self.repository)
        if self.branch is not None:
            filt['branch'] = self.branch
        _schedulers.append(schedulers.AnyBranchScheduler(
            name=spawner_name,
            builderNames=[spawner_name],
            change_filter=util.ChangeFilter(**filt),
            onlyImportant=True,
            fileIsImportant=importantManager.fileIsImportant,
            codebases=codebases,
            ))
        _schedulers.append(schedulers.ForceScheduler(
            name="force" + spawner_name,
            builderNames=[spawner_name],
            codebases=self.createCodebaseParams(codebases)))



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


def getSupportedVCSTypes():
    plugins = get_plugins("travis", IVCSManager, load_now=False)
    return {vcs_type: plugins.get(vcs_type).description for vcs_type in plugins.names}


def addRepository(name, config):
    global repository_db
    vcs_type = config['vcs_type']
    plugins = get_plugins("travis", IVCSManager, load_now=False)
    if vcs_type in plugins.names:
        plugin = plugins.get(vcs_type)
        r = repository_db[name] = plugin(**config)
        return r

    raise KeyError("No VCS manager for %s, got %s" % (vcs_type, plugins.info_all()))
