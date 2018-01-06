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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from future.moves.urllib.parse import urlparse

from buildbot.plugins import changes
from buildbot.steps.source.git import Git

from .base import PollerMixin, VCSBase


class ParsedGitUrl(object):
    def __init__(self, url):
        parsed = urlparse(url)
        self.netloc = parsed.netloc
        self.path = parsed.path
        self.scheme = parsed.scheme
        self.user = None
        self.port = None
        if "@" in self.netloc:
            self.user, self.netloc = self.netloc.split("@")
            if ":" in self.user:
                self.user, self.passwd = self.user.split(":", 1)
        if ":" in self.netloc:
            self.netloc, self.port = self.netloc.rsplit(":", 1)
            self.port = int(self.port)


class GitBase(VCSBase):
    GitStep = Git
    shallow = False
    method = "clone"
    mode = "incremental"
    retryFetch = True
    retry = (2, 10)  # default retry 10 times, with 2 seconds delay

    def addRepository(self, factory, project=None, repository=None, branches=None, **kwargs):
        kwargs.update(dict(
            repourl=repository,
            codebase=project,
            haltOnFailure=True,
            flunkOnFailure=True,
            getDescription={'tags': True, 'always': True},
            shallow=self.shallow,
            mode=self.mode,
            method=self.method,
            retryFetch=self.retryFetch,
            retry=self.retry
        ))

        factory.addStep(self.GitStep(**kwargs))


class GitPoller(GitBase, PollerMixin):
    description = "Source code hosted on git, with detection of changes using poll method"

    def setupChangeSource(self, changeSources):
        pollerdir = self.makePollerDir(self.name)
        changeSources.append(changes.GitPoller(
            repourl=self.repository,
            workdir=pollerdir,
            project=self.name,
            branch=self.branch
        ))


class GitPb(GitBase):
    description = "Source code hosted on git, with detection of changes using git hooks method"

    def setupChangeSource(self, changeSources):
        pass
