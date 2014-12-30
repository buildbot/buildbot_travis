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

from .base import VCSBase, PollerMixin
from buildbot.changes import gitpoller
from buildbot.steps.source.git import Git


class GitBase(VCSBase):

    def addRepository(self, factory, project=None, repository=None, branch=None, **kwargs):
        branch = branch or "master"
        kwargs.update(dict(
            repourl=repository,
            branch=branch,
            codebase=project,
            haltOnFailure=True,
            flunkOnFailure=True,
        ))

        factory.addStep(Git(**kwargs))


class GitPoller(GitBase, PollerMixin):

    def setupChangeSource(self, changeSources):
        pollerdir = self.makePollerDir(self.name)
        changeSources.append(gitpoller.GitPoller(
            repourl=self.repository,
            workdir=pollerdir,
            project=self.name
            ))


class GitPb(GitBase):

    def setupChangeSource(self, changeSources):
        pass


class Github(GitBase):

    def setupChangeSource(self, changeSources):
        pass
