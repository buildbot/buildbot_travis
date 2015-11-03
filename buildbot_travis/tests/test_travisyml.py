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

from buildbot_travis.travisyml import TravisYml, TravisYmlInvalid


class TravisYmlTestCase(unittest.TestCase):

    def setUp(self):
        self.t = TravisYml()
        self.t.config = {}


class TestEnv(TravisYmlTestCase):

    def test_noenv(self):
        self.t.parse_envs()
        self.failUnlessEqual(self.t.environments, [{}])

    def test_singleenv(self):
        self.t.config["env"] = "FOO=1 BAR=2"
        self.t.parse_envs()
        self.failUnlessEqual(self.t.environments, [dict(FOO='1', BAR='2')])

        self.t.parse_matrix()
        self.failUnlessEqual(
            self.t.matrix, [dict(python="python2.6", env=dict(FOO='1', BAR='2')), ])

    def test_multienv(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        self.t.parse_envs()
        self.failUnlessEqual(
            self.t.environments, [dict(FOO='1', BAR='2'), dict(FOO='2', BAR='1')])

        self.t.parse_matrix()
        self.failUnlessEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1')),
        ])

    def test_globalenv(self):
        self.t.config["env"] = {'global': ["FOOBAR=0"], 'matrix': ["FOO=1 BAR=2", "FOO=2 BAR=1"]}
        self.t.parse_envs()
        self.failUnlessEqual(
            self.t.environments, [dict(FOOBAR='0', FOO='1', BAR='2'), dict(FOOBAR='0', FOO='2', BAR='1')])

        self.t.parse_matrix()
        self.failUnlessEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOOBAR='0', FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOOBAR='0', FOO='2', BAR='1')),
        ])

    def test_emptymatrixlenv(self):
        self.t.config["env"] = {'global': ["FOOBAR=0"]}
        self.t.parse_envs()
        self.failUnlessEqual(
            self.t.environments, [dict(FOOBAR='0')])

        self.t.parse_matrix()
        self.failUnlessEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOOBAR='0')),
        ])


class TestMatrix(TravisYmlTestCase):

    def test_exclude_match(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="python2.6", env="FOO=2 BAR=1")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.failUnlessEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
        ])

    def test_exclude_nomatch(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="python2.6", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.failUnlessEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1')),
        ])

    def test_include(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['include'] = [dict(python="python2.6", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.failUnlessEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1')),
            dict(python="python2.6", env=dict(FOO='2', BAR='3')),
        ])


class TestHooks(TravisYmlTestCase):

    def test_empty(self):
        self.t.parse_hooks()
        self.failUnlessEqual(self.t.before_install, [])
        self.failUnlessEqual(self.t.install, [])
        self.failUnlessEqual(self.t.after_install, [])
        self.failUnlessEqual(self.t.before_script, [])
        self.failUnlessEqual(self.t.script, [])
        self.failUnlessEqual(self.t.after_script, [])

    def test_single(self):
        self.t.config["after_script"] = "wibble -f foo"
        self.t.parse_hooks()
        self.failUnlessEqual(self.t.after_script, ["wibble -f foo"])

    def test_multi(self):
        self.t.config["after_script"] = ["wibble -f foo", "fox"]
        self.t.parse_hooks()
        self.failUnlessEqual(self.t.after_script, ["wibble -f foo", "fox"])


class TestBranches(TravisYmlTestCase):

    def test_nobranches(self):
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, None)
        self.failUnlessEqual(self.t.branch_blacklist, None)
        self.failUnlessEqual(self.t.can_build_branch("master"), True)

    def test_whitelist(self):
        self.t.config["branches"] = {"only": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, ["master"])
        self.failUnlessEqual(self.t.branch_blacklist, None)
        self.failUnlessEqual(self.t.can_build_branch("master"), True)
        self.failUnlessEqual(
            self.t.can_build_branch("feature-new-stuff"), False)

    def test_whitelist_regex(self):
        self.t.config["branches"] = {"only": ['master', '/^deploy-.*$/']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.can_build_branch("master"), True)
        self.failUnlessEqual(self.t.can_build_branch("wibble"), False)
        self.failUnlessEqual(
            self.t.can_build_branch("deploy-cool-regex"), True)

    def test_blacklist(self):
        self.t.config["branches"] = {"except": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, None)
        self.failUnlessEqual(self.t.branch_blacklist, ["master"])
        self.failUnlessEqual(self.t.can_build_branch("master"), False)
        self.failUnlessEqual(
            self.t.can_build_branch("feature-new-stuff"), True)

    def test_whitelist_and_blacklist(self):
        """ Test that blacklist is ignored when both whitelist and blacklist are present """
        self.t.config["branches"] = {
            "only": ['master'], "except": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, ["master"])
        self.failUnlessEqual(self.t.branch_blacklist, None)
        self.failUnlessEqual(self.t.can_build_branch("master"), True)
        self.failUnlessEqual(
            self.t.can_build_branch("feature-new-stuff"), False)


class TestMailNotifications(TravisYmlTestCase):

    def test_nomail(self):
        self.t.parse_notifications_email()
        self.assertEqual(self.t.email.enabled, False)
        self.assertEqual(self.t.email.success, "change")
        self.assertEqual(self.t.email.failure, "always")

    def test_mail_on_success(self):
        b = self.t.config["notifications"] = {}
        b["email"] = {"on_success": "never"}
        self.t.parse_notifications_email()
        self.assertEqual(self.t.email.enabled, True)
        self.assertEqual(self.t.email.success, "never")
        self.assertEqual(self.t.email.failure, "always")

    def test_mail_on_success_fail(self):
        n = self.t.config["notifications"] = {}
        n["email"] = {"on_success": "wibble"}
        self.assertRaises(TravisYmlInvalid, self.t.parse_notifications_email)

    def test_mail_on_failure(self):
        n = self.t.config["notifications"] = {}
        n["email"] = {"on_failure": "never"}
        self.t.parse_notifications_email()
        self.assertEqual(self.t.email.enabled, True)
        self.assertEqual(self.t.email.success, "change")
        self.assertEqual(self.t.email.failure, "never")

    def test_mail_on_failure_fail(self):
        n = self.t.config["notifications"] = {}
        n["email"] = {"on_failure": "wibble"}
        self.assertRaises(TravisYmlInvalid, self.t.parse_notifications_email)

    def test_mail_off(self):
        n = self.t.config["notifications"] = {}
        n["email"] = False
        self.t.parse_notifications_email()
        self.assertEqual(self.t.email.enabled, False)


class TestIrcNotifications(TravisYmlTestCase):

    def test_noirc(self):
        self.t.parse_notifications_irc()
        self.assertEqual(self.t.irc.enabled, False)

    def test_channels(self):
        channels = [
            "irc.freenode.org#travis",
            "irc.freenode.org#some-other-channel"
        ]

        n = self.t.config["notifications"] = {}
        n["irc"] = dict(channels=channels[:])
        self.t.parse_notifications_irc()

        self.assertEqual(self.t.irc.enabled, True)
        self.assertEqual(self.t.irc.channels, channels)
