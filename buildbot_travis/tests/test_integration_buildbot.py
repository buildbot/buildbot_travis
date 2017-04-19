# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from __future__ import absolute_import, division, print_function

import os
import shutil
import tempfile
import unittest

from twisted.internet import defer

import buildbot
from buildbot.worker.local import LocalWorker
from buildbot_travis.steps.create_steps import TravisSetupSteps

try:
    from buildbot.test.util.integration import RunMasterBase
except ImportError:
    # if buildbot installed with wheel, it does not include the test util :-(
    RunMasterBase = object


# this test is and easy way to create a master with lots of data in it
# it runs the bbtravis of buildbot which is expected to be in development mode
# and disable the setup steps to create build quickly
# with it you can see how the dashboard behaves when buildbot is creating lots of stuff

class TravisMaster(RunMasterBase):
    timeout = 30000

    def mktemp(self):
        # twisted mktemp will create a very long directory, which virtualenv will not like.
        # https://github.com/pypa/virtualenv/issues/596
        # so we put it in the /tmp directory to be safe
        tmp = tempfile.mkdtemp(prefix="travis_trial")
        self.addCleanup(shutil.rmtree, tmp)
        return os.path.join(tmp, "work")

    @defer.inlineCallbacks
    def test_debug_dashboards(self):
        raise unittest.SkipTest("test should only be enabled to debug dashboards with real'ish data")
        from git import Repo
        self.patch(TravisSetupSteps, 'disable', True)
        yield self.setupConfig(masterConfig(), startWorker=False)
        repo = Repo(path_to_repo)
        for c in repo.iter_commits('HEAD', max_count=15):
            change = dict(branch="master",
                          files=["foo.c"],
                          author=c.author.name + " <" + c.author.email + ">",
                          comments=c.message,
                          revision=c.hexsha,
                          repository=path_to_repo,
                          project="buildbot"
                          )
            yield self.doForceBuild(wantSteps=True, useChange=change, wantLogs=True)
        # wait forever
        yield defer.Deferred()


# master configuration
sample_yml = """
projects:
  - name: buildbot
    repository: %(path_to_repo)s
    vcs_type: git+poller
"""

path_to_repo = None


def masterConfig():
    global path_to_repo
    from buildbot_travis import TravisConfigurator
    path_to_repo = os.path.dirname(buildbot.__file__)
    while not os.path.exists(os.path.join(path_to_repo, ".git")) and len(path_to_repo) > 1:
        path_to_repo = os.path.dirname(path_to_repo)
    with open("sample.yml", "w") as f:
        f.write(sample_yml % dict(path_to_repo=path_to_repo))
    c = {}
    c['workers'] = [LocalWorker("local2"), LocalWorker("local3")]
    TravisConfigurator(c, os.getcwd()).fromYaml("sample.yml")
    return c
