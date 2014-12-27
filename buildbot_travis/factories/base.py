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

from buildbot.process import factory
from buildbot.steps.source.svn import SVN
from buildbot.steps.source.git import Git


class BaseFactory(factory.BuildFactory):

    """
    Generic factory that deals with SVN (or Git)
    """

    def __init__(self, projectname, repository, vcs_type=None, branch=None, username=None, password=None, subrepos=None):
        factory.BuildFactory.__init__(self, [])
        self.addRepository(
            projectname, repository, vcs_type, branch, username, password)
        if subrepos:
            for subrepo in subrepos:
                self.addRepository(
                    **subrepo
                )

    def addRepository(self, project=None, repository=None, vcs_type=None, branch=None, username=None, password=None, **kwargs):
        kwargs = dict(kwargs)

        if not vcs_type:
            if repository.startswith("https://svn."):
                vcs_type = "svn"
            elif repository.startswith("git://github.com/"):
                vcs_type = "git"

        if not branch:
            branch = dict(svn="trunk", git="master")[vcs_type]

        if vcs_type == "svn":
            kwargs.update(dict(
                baseURL=repository,
                defaultBranch=branch,
                username=username,
                password=password,
                codebase=project,
            ))

            self.addStep(SVN(**kwargs))

        elif vcs_type == "git":
            kwargs.update(dict(
                repourl=repository,
                branch=branch,
                codebase=project,
            ))

            self.addStep(Git(**kwargs))
