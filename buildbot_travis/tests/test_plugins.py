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


class VCSTestCaseGitPb(VCSTestCase):
    sample_repo = dict(name="repo", vcs_type="git+pbhook", repository="foo", branch="bar")


class VCSTestCaseGitGitHubHook(VCSTestCase):
    sample_repo = dict(name="repo", vcs_type="git+githubhook", repository="foo", branch="bar")
