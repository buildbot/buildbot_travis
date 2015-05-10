# Copyright 2014-2013 Isotoma Limited
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

from .git import GitBase, ParsedGitUrl
from buildbot.plugins import changes
from buildbot.plugins import util
from buildbot.plugins import schedulers
from buildbot.steps.source.gerrit import Gerrit as GerritStep

from buildbot import config
from twisted.internet import defer


class GerritChangeSource(changes.GerritChangeSource):
    watchedRepos = None

    def __init__(self, *args, **kw):
        changes.GerritChangeSource.__init__(self, *args, **kw)
        self.watchedRepos = {}

    def addChange(self, chdict):
        props = chdict['properties']
        branch = props.get('event.change.branch', chdict.get('branch'))
        k = chdict.get('project', '') + ":" + branch
        if k in self.watchedRepos:
            chdict['project'] = self.watchedRepos[k]
            props['event.change.branch'] = branch
            return changes.GerritChangeSource.addChange(self, chdict)
        return defer.succeed(None)

    def watchRepository(self, path, branch, projectName):
        path = path.lstrip("/")
        self.watchedRepos[path + ':' + branch] = projectName


class GerritChangeSourceManager(object):
    sources = {}

    def makeGerritChangeSource(self, projectName, server, port, user, path, branch):
        k = "%s:%d:%s" % (server, port, user)
        if k not in self.sources:
            cs = GerritChangeSource(gerritserver=server, gerritport=port, username=user)
            self.sources[k] = cs
        else:
            cs = self.sources[k]
        cs.watchRepository(path, branch, projectName)
        return cs
manager = GerritChangeSourceManager()


class Gerrit(GitBase):
    description = "Source code hosted on Gerrit, with detection of changes using gerrit stream-events"
    supportsTry = True

    def addRepository(self, factory, project=None, repository=None, branch=None, **kwargs):
        branch = branch or "master"
        kwargs.update(dict(
            repourl=repository,
            branch=branch,
            codebase=project,
            haltOnFailure=True,
            flunkOnFailure=True,
            retryFetch=True
        ))

        factory.addStep(GerritStep(**kwargs))

    def setupChangeSource(self, changeSources):
        parsed = ParsedGitUrl(self.repository)
        if parsed.scheme not in ("ssh",):
            config.error("Only ssh:// repository urls are supported :%s" % (self.repository,))
        if parsed.user is None:
            config.error("Please define gerrit user in repository url :%s" % (self.repository,))
        if parsed.port is None:
            config.error("Please define gerrit port in repository url :%s" % (self.repository,))

        cs = manager.makeGerritChangeSource(self.name, parsed.netloc,
                                            parsed.port, parsed.user, parsed.path, self.branch)
        if cs and cs not in changeSources:
            changeSources.append(cs)

    def setupSchedulers(self, _schedulers, spawner_name, try_name, importantManager, codebases):

        _schedulers.append(schedulers.AnyBranchScheduler(
            name=spawner_name,
            builderNames=[spawner_name],
            change_filter=util.GerritChangeFilter(branch=self.branch, project=self.name,
                                                  eventtype="ref-updated"),
            onlyImportant=True,
            fileIsImportant=importantManager.fileIsImportant,
            codebases=codebases,
            ))
        _schedulers.append(schedulers.AnyBranchScheduler(
            name=try_name,
            builderNames=[try_name],
            change_filter=util.GerritChangeFilter(branch=self.branch, project=self.name,
                                                  eventtype="patchset-created"),
            onlyImportant=True,
            fileIsImportant=importantManager.fileIsImportant,
            codebases=codebases,
            ))
        _schedulers.append(schedulers.ForceScheduler(
            name="force" + spawner_name,
            builderNames=[spawner_name],
            codebases=self.createCodebaseParams(codebases)))
