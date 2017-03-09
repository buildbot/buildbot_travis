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

import os

from .base import VCSBase, PollerMixin
from buildbot_travis.changes import svnpoller
import subprocess
from buildbot.steps.source.svn import SVN
from twisted.python import log

# XXX untested code!


class SVNChangeSplitter(object):

    def __init__(self, repository):
        self.repository = repository
        self.roots = []

    def add(self, repository, branch, project):
        assert repository.startswith(self.repository)
        repository = repository[len(self.repository):]
        self.roots.append((repository, branch, project))

    def split_file(self, path):
        pieces = path.split("/")
        if pieces[0] == 'trunk':
            return 'trunk', '/'.join(pieces[1:])
        elif pieces[0] == 'branches':
            return '/'.join(pieces[0:2]), '/'.join(pieces[2:])
        return None

    def __call__(self, path):
        log.msg("Looking for match for '%s'" % path)
        for root, branch, project in self.roots:
            if path.startswith(root):
                log.msg("Found match - project '%s'" % project)
                f = svnpoller.SVNFile()
                f.project = project
                f.repository = self.repository + root
                path = path[len(root):]
                if not branch:
                    log.msg("Determining branch")
                    where = self.split_file(path)
                    if where is None:
                        return None
                    f.branch, f.path = where  # noqa
                else:
                    log.msg("Trying to force branch")
                    if not path.startswith(branch):
                        log.msg("'%s' doesnt start with '%s'" % (path, branch))
                        continue
                    f.branch = branch
                    f.path = path[len(branch):]
                return f
        log.msg("No match found")
        log.msg(self.roots)


class SVNPoller(VCSBase, PollerMixin):
    description = "Source code hosted on svn, with detection of changes using poll method"
    repositories = {}  # class variable!
    username = None
    password = None
    subrepos = None

    def addRepository(self, factory, project=None, repository=None, branch=None, **kwargs):
        kwargs = dict(kwargs)

        branch = branch or "trunk"

        kwargs.update(dict(
            baseURL=repository,
            defaultBranch=branch,
            username=self.username,
            password=self.password,
            codebase=project,
            haltOnFailure=True,
            flunkOnFailure=True,
        ))

        factory.addStep(SVN(**kwargs))

    def getRepositoryRoot(self):
        options = {}
        cmd = ["svn", "info", self.repository, "--non-interactive"]
        if self.username:
            cmd.extend(["--username", self.username])
        if self.password:
            cmd.extend(["--password", self.password])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env={'LC_MESSAGES': 'C'})
        s, _ = p.communicate()
        for line in s.split("\n"):
            if ":" in line:
                k, v = line.split(": ")
                k = k.strip().lower().replace(" ", "-")
                v = v.strip()
                options[k] = v
        return options["repository-root"] + "/"

    def setupChangeSource(self, changeSources):
        for repo in self.repositories:
            if self.repository.startswith(repo):
                splitter = self.repositories[repo]
                break
        else:
            repo = self.getRepositoryRoot()

            scheme, netloc, path, _, _, _ = urlparse(repo)
            name = "%s-%s-%s" % (scheme, netloc.replace(".", "-"), path.rstrip("/").lstrip("/").replace("/", "-"))
            pollerdir = self.makePollerDir(name)

            splitter = self.repositories[repo] = SVNChangeSplitter(repo)

            changeSources.append(svnpoller.SVNPoller(
                repourl=repo,
                cachepath=os.path.join(pollerdir, "pollerstate"),
                project=None,
                split_file=splitter,
                svnuser=self.username,
                svnpasswd=self.password,
                ))

        splitter.add(self.repository, self.branch, self.name)
