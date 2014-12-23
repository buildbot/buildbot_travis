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

import os

from buildbot.test.util.integration import RunMasterBase
from twisted.internet import defer
from subprocess import check_call
from buildbot.buildslave import BuildSlave
from buildbot.buildslave import AbstractLatentBuildSlave
from buildbot import util

# This integration test creates a master and slave environment,
# with one builder and a custom step
# The custom step is using a CustomService, in order to calculate its result
# we make sure that we can reconfigure the master while build is running


class TravisMaster(RunMasterBase):

    @defer.inlineCallbacks
    def test_travis(self):
        change = dict(branch="master",
                      files=["foo.c"],
                      author="me@foo.com",
                      comments="good stuff",
                      revision="HEAD",
                      project="buildbot_travis"
                      )
        build = yield self.doForceBuild(wantSteps=True, useChange=change, wantLogs=True)

        self.assertEqual(build['steps'][0]['state_string'], 'update buildbot_travis')
        self.assertEqual(build['steps'][1]['state_string'], 'triggered ' +
                         ", ".join(["buildbot_travis-job"] * 6))
        builds = yield self.master.data.get(("builds",))
        self.assertEqual(len(builds), 7)

# master configuration

sample_yml = """
projects:
  - name: buildbot_travis
    repository: %(path_to_git_bundle)s
    vcs_type: git
"""


def masterConfig():
    from buildbot_travis import TravisConfigurator
    path_to_git_bundle = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.git.bundle"))
    with open("sample.yml", "w") as f:
        f.write(sample_yml % dict(path_to_git_bundle=path_to_git_bundle))
    c = {}
    c['slaves'] = [BuildSlave("local1", "p"), AbstractLatentBuildSlave("local1", "p")]
    TravisConfigurator(c, os.getcwd()).fromYaml("sample.yml")
    return c
