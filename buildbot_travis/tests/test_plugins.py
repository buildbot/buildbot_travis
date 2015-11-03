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

import shutil

from twisted.trial import unittest

from buildbot_travis.vcs import addRepository


class VCSTestCase(unittest.TestCase):
    sample_repo = dict(name="repo", vcs_type="git+poller", repository="foo", branch="bar")

    def setUp(self):
        self.vcs = addRepository("repo", self.sample_repo)
        self.vcs.vardir = ""

    def test_source(self):
        cs = []
        self.vcs.setupChangeSource(cs)


class VCSTestCaseSVNPoller(VCSTestCase):
    def setUp(self):
        self.skipTest("svn is not integrated")
        # check_call(["svnadmin", "create", "foo.svn"])
        # repo = "file://" + os.getcwd() + "/foo.svn/"
        # check_call(["svn", "co", repo, 'foo'], stdout=subprocess.PIPE)
        # self.sample_repo['repository'] = repo
        # VCSTestCase.setUp(self)

    sample_repo = dict(name="repo", vcs_type="svn+poller", branch="bar")

    def tearDown(self):
        shutil.rmtree("foo")
        shutil.rmtree("foo.svn")


class VCSTestCaseGitGitHubHook(VCSTestCase):
    sample_repo = dict(name="repo", vcs_type="gerrit", repository="ssh://foo@bar:29418/repo", branch="bar")
