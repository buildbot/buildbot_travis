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

import os

from buildbot.plugins import reporters, steps, util

from .base import getCodebaseForRepository
from .git import GitBase


def getCodebaseForGitHubChange(payload):
    return getCodebaseForRepository(payload['repository']['html_url'])


@util.renderer
def makeContext(props):
    if "reason" not in props:
        return "buildbot"
    return "buildbot" + ":" + props.getProperty("reason")


class GitHub(GitBase):
    description = "Source code hosted on github, with detection of changes using github web hooks"
    supportsTry = True
    github_token = None
    reporter_context = ""
    default_reporter_context = "bb%(prop:matrix_label:+/)s%(prop:matrix_label)s"

    # GitHub is only in 0.9.1+
    if hasattr(steps, "GitHub"):
        GitStep = steps.GitHub

    def getPushChangeFilter(self):
        filt = dict(repository=self.repository)
        filt['category'] = None
        if self.branch is not None:
            filt['branch'] = self.branch
        return util.ChangeFilter(**filt)

    def getTryChangeFilter(self):
        filt = dict(repository=self.repository)
        filt['category'] = 'pull'
        return util.ChangeFilter(**filt)

    def setupChangeSource(self, changeSources):
        return {'github': {'codebase': getCodebaseForGitHubChange}}

    def setupReporters(self, _reporters, spawner_name, try_name, codebases):
        name = "GitHubStatusPush"
        reportersByName = dict([(r.name, r) for r in _reporters])
        if name not in reportersByName and self.github_token:
            token = self.github_token
            if token.startswith("file:"):
                with open(token.split(":", 2)[1]) as f:
                    token = f.read().strip()
            if token.startswith("env:"):
                token = os.environ[token.split(":", 2)[1]]
            if not self.reporter_context:
                self.reporter_context = self.default_reporter_context
            _reporters.append(
                reporters.GitHubStatusPush(token, context=util.Interpolate(self.reporter_context),
                                           verbose=True))
