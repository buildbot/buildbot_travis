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

import fnmatch

from .git import GitBase, ParsedGitUrl
from buildbot.plugins import changes
from buildbot.plugins import util
from buildbot.plugins import schedulers
from buildbot.steps.source.gerrit import Gerrit as GerritStep
from buildbot.plugins import reporters

from buildbot import config
from twisted.internet import defer
from buildbot.util import ComparableMixin


class RepoMatcher(ComparableMixin):
    compare_attrs = ("path", "branches", "project")

    def __init__(self, path, branches, project):
        self.path = path
        self.branches = branches
        self.project = project

    def match(self, chdict):
        props = chdict['properties']
        branch = props.get('event.change.branch', chdict.get('branch'))
        if chdict.get('project', '') != self.path:
            return False
        for b in self.branches:
            if fnmatch.fnmatch(branch, b):
                print "match", branch, b
                return True
        return False


class GerritChangeSource(changes.GerritChangeSource):
    watchedRepos = None
    compare_attrs = ("gerritserver", "gerritport", "watchedRepos")

    def __init__(self, *args, **kw):
        changes.GerritChangeSource.__init__(self, *args, **kw)
        self.watchedRepos = {}
        self.configureService()

    def reconfigServiceWithSibling(self, sibling):
        print "reconfiguring", self.name, sibling.watchedRepos
        self.watchedRepos = sibling.watchedRepos
        return changes.GerritChangeSource.reconfigServiceWithSibling(self, sibling)

    def addChange(self, chdict):
        project = chdict.get('project', '')
        props = chdict['properties']
        branch = props.get('event.change.branch', chdict.get('branch'))
        for m in self.watchedRepos.get(project, []):
            if m.match(chdict):
                chdict['project'] = m.project
                props['event.change.branch'] = branch
                return changes.GerritChangeSource.addChange(self, chdict)
        return defer.succeed(None)

    def watchRepository(self, path, branches, projectName):
        path = path.lstrip("/")
        self.watchedRepos.setdefault(path, [])
        self.watchedRepos[path].append(RepoMatcher(path, branches, projectName))


class GerritChangeSourceManager(object):
    sources = {}

    def makeGerritChangeSource(self, projectName, server, port, user, path, branches):
        k = "%s:%d:%s" % (server, port, user)
        if k not in self.sources:
            cs = GerritChangeSource(gerritserver=server, gerritport=port, username=user)
            self.sources[k] = cs
        else:
            cs = self.sources[k]
        cs.watchRepository(path, branches, projectName)
        return cs
manager = GerritChangeSourceManager()


class Gerrit(GitBase):
    description = "Source code hosted on Gerrit, with detection of changes using gerrit stream-events"
    supportsTry = True

    def addRepository(self, factory, project=None, repository=None, branches=None, **kwargs):
        kwargs.update(dict(
            repourl=repository,
            branch=util.Property("branch"),
            codebase=project,
            haltOnFailure=True,
            flunkOnFailure=True,
            retryFetch=True,
            getDescription={'tags': True, 'always': True}
        ))

        factory.addStep(GerritStep(**kwargs))

    def parseServerURL(self):
        parsed = ParsedGitUrl(self.repository)
        if parsed.scheme not in ("ssh",):
            config.error("Only ssh:// repository urls are supported :%s" % (self.repository,))
        if parsed.user is None:
            config.error("Please define gerrit user in repository url :%s" % (self.repository,))
        if parsed.port is None:
            config.error("Please define gerrit port in repository url :%s" % (self.repository,))
        return parsed

    def setupChangeSource(self, changeSources):
        parsed = self.parseServerURL()
        cs = manager.makeGerritChangeSource(self.name, parsed.netloc,
                                            parsed.port, parsed.user, parsed.path, self.branches)
        if cs and cs not in changeSources:
            changeSources.append(cs)

    def setupSchedulers(self, _schedulers, spawner_name, try_name, deploy_name, importantManager, codebases, dep_properties):
        # branch filtering is already made by the changesource
        _schedulers.append(schedulers.AnyBranchScheduler(
            name=spawner_name,
            builderNames=[spawner_name],
            change_filter=util.GerritChangeFilter(project=self.name,
                                                  eventtype_re="ref-updated"),
            onlyImportant=True,
            fileIsImportant=importantManager.fileIsImportant,
            codebases=codebases,
            ))
        _schedulers.append(schedulers.AnyBranchScheduler(
            name=try_name,
            builderNames=[try_name],
            change_filter=util.GerritChangeFilter(project=self.name,
                                                  eventtype="patchset-created"),
            onlyImportant=True,
            fileIsImportant=importantManager.fileIsImportant,
            codebases=codebases,
            ))
        _schedulers.append(schedulers.ForceScheduler(
            name="force" + spawner_name,
            builderNames=[spawner_name],
            codebases=self.createCodebaseParams(codebases)))

        _schedulers.append(schedulers.ForceScheduler(
            name=deploy_name,
            builderNames=[deploy_name],
            codebases=self.createCodebaseParamsForDeploy(codebases),
            properties=dep_properties))

    def setupReporters(self, _reporters, spawner_name, try_name, codebases):
        parsed = self.parseServerURL()
        name = "GerritReporter(%s,%d,%s)" % (parsed.netloc, parsed.port, parsed.user)
        reportersByName = dict([(r.name, r) for r in _reporters])
        if name not in reportersByName:
            builders = []
            reporter = reporters.GerritStatusPush(server=parsed.netloc, port=parsed.port,
                                                  username=parsed.user, builders=builders)
            reporter.name = name
            # the normal workflow is that builders attribute would be set at service configure stage
            # not at service instanciation.
            # but as we need to append the builders list during the config, this is important
            # to modify the list we pass as configuration.
            reporter.builders = builders
            _reporters.append(reporter)
            reportersByName[name] = reporter
        reportersByName[name].builders.append(try_name)
