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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import yaml
from twisted.trial import unittest

from buildbot.plugins import steps, util
from buildbot_travis.travisyml import TravisYml, TravisYmlInvalid


class TravisYmlTestCase(unittest.TestCase):

    def setUp(self):
        self.t = TravisYml()
        self.t.config = {}


class TestYamlParsing(TravisYmlTestCase):

    def test_basic(self):
        self.t.parse("""
        language: python
        """)

    def test_with_scripts(self):
        self.t.parse("""
        language: python
        script:
            - echo ok
        """)
        self.failUnlessEqual(self.t.script, ["echo ok"])

    def test_with_interpolated_scripts(self):
        self.t.parse("""
        language: python
        script:
            - !i echo ok
        """)
        self.failUnlessEqual(self.t.script, [util.Interpolate("echo ok")])

    def test_with_interpolated_scripts_in_list(self):
        self.t.parse("""
        language: python
        script:
          - title: make dist
            cmd: [ "make", !Interpolate "REVISION=%(prop:got_revision:-%(src::revision:-unknown)s)s", "dist" ]
        """)
        self.failUnlessEqual(self.t.script, [{'cmd': [
            'make',
            util.Interpolate(u'REVISION=%(prop:got_revision:-%(src::revision:-unknown)s)s'),
            'dist'],
            'title': 'make dist'}])

    def test_with_plugin_step(self):
        if not hasattr(steps.CMake, "compare_attrs"):
            return unittest.SkipTest("Test needs buildbot buildstep comparison")
        self.t.parse("""
        language: python
        script:
            - !CMake target
        """)
        self.failUnlessEqual(self.t.script, [steps.CMake("target")])

    def test_with_plugin_step_with_parse_error(self):
        self.assertRaises(TravisYmlInvalid, self.t.parse, """
        language: python
        script:
            - !CMake [ tar:get ]
        """)

    def test_yaml_not_polluted(self):
        """yaml.load should not recognise Interpolate contruct"""
        self.assertRaises(yaml.constructor.ConstructorError, yaml.load, """
            - !i foo
            """)

class TestEnv(TravisYmlTestCase):

    def test_noenv(self):
        self.t.parse_envs()
        self.assertEqual(self.t.environments, [{}])

    def test_singleenv(self):
        self.t.config["env"] = "FOO=1 BAR=2"
        self.t.parse_envs()
        self.assertEqual(self.t.environments, [dict(FOO='1', BAR='2')])

        self.t.parse_matrix()
        self.assertEqual(
            self.t.matrix, [dict(python="python2.6", env=dict(FOO='1', BAR='2')), ])

    def test_multienv(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        self.t.parse_envs()
        self.assertEqual(
            self.t.environments, [dict(FOO='1', BAR='2'), dict(FOO='2', BAR='1')])

        self.t.parse_matrix()
        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1')),
        ])

    def test_globalenv(self):
        self.t.config["env"] = {'global': ["FOOBAR=0"], 'matrix': ["FOO=1 BAR=2", "FOO=2 BAR=1"]}
        self.t.parse_envs()
        self.assertEqual(
            self.t.environments, [dict(FOOBAR='0', FOO='1', BAR='2'), dict(FOOBAR='0', FOO='2', BAR='1')])

        self.t.parse_matrix()
        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOOBAR='0', FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOOBAR='0', FOO='2', BAR='1')),
        ])

    def test_emptymatrixlenv(self):
        self.t.config["env"] = {'global': ["FOOBAR=0"]}
        self.t.parse_envs()
        self.assertEqual(
            self.t.environments, [dict(FOOBAR='0')])

        self.t.parse_matrix()
        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOOBAR='0')),
        ])


class TestMatrix(TravisYmlTestCase):

    def test_exclude_match(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="python2.6", env="FOO=2 BAR=1")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
        ])

    def test_exclude_subset_match(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1 SPAM=3"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="python2.6", env="FOO=2 BAR=1")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
        ])

    def test_exclude_nomatch(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="python2.6", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1')),
        ])

    def test_include(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['include'] = [dict(python="python2.6", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1')),
            dict(python="python2.6", env=dict(FOO='2', BAR='3')),
        ])

    def test_include_with_global(self):
        self.t.config["env"] = {'global': "CI=true", 'matrix': ["FOO=1 BAR=2", "FOO=2 BAR=1"]}
        m = self.t.config["matrix"] = {}
        m['include'] = [dict(python="python2.6", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="python2.6", env=dict(FOO='1', BAR='2', CI='true')),
            dict(python="python2.6", env=dict(FOO='2', BAR='1', CI='true')),
            dict(python="python2.6", env=dict(FOO='2', BAR='3', CI='true')),
        ])


class TestHooks(TravisYmlTestCase):

    def test_empty(self):
        self.t.parse_hooks()
        self.assertEqual(self.t.before_install, [])
        self.assertEqual(self.t.install, [])
        self.assertEqual(self.t.after_install, [])
        self.assertEqual(self.t.before_script, [])
        self.assertEqual(self.t.script, [])
        self.assertEqual(self.t.after_script, [])

    def test_single(self):
        self.t.config["after_script"] = "wibble -f foo"
        self.t.parse_hooks()
        self.assertEqual(self.t.after_script, ["wibble -f foo"])

    def test_multi(self):
        self.t.config["after_script"] = ["wibble -f foo", "fox"]
        self.t.parse_hooks()
        self.assertEqual(self.t.after_script, ["wibble -f foo", "fox"])


class TestBranches(TravisYmlTestCase):

    def test_nobranches(self):
        self.t.parse_branches()
        self.assertEqual(self.t.branch_whitelist, None)
        self.assertEqual(self.t.branch_blacklist, None)
        self.assertEqual(self.t.can_build_branch("master"), True)

    def test_whitelist(self):
        self.t.config["branches"] = {"only": ['master']}
        self.t.parse_branches()
        self.assertEqual(self.t.branch_whitelist, ["master"])
        self.assertEqual(self.t.branch_blacklist, None)
        self.assertEqual(self.t.can_build_branch("master"), True)
        self.assertEqual(
            self.t.can_build_branch("feature-new-stuff"), False)

    def test_whitelist_regex(self):
        self.t.config["branches"] = {"only": ['master', '/^deploy-.*$/']}
        self.t.parse_branches()
        self.assertEqual(self.t.can_build_branch("master"), True)
        self.assertEqual(self.t.can_build_branch("wibble"), False)
        self.assertEqual(
            self.t.can_build_branch("deploy-cool-regex"), True)

    def test_blacklist(self):
        self.t.config["branches"] = {"except": ['master']}
        self.t.parse_branches()
        self.assertEqual(self.t.branch_whitelist, None)
        self.assertEqual(self.t.branch_blacklist, ["master"])
        self.assertEqual(self.t.can_build_branch("master"), False)
        self.assertEqual(
            self.t.can_build_branch("feature-new-stuff"), True)

    def test_whitelist_and_blacklist(self):
        """ Test that blacklist is ignored when both whitelist and blacklist are present """
        self.t.config["branches"] = {
            "only": ['master'], "except": ['master']}
        self.t.parse_branches()
        self.assertEqual(self.t.branch_whitelist, ["master"])
        self.assertEqual(self.t.branch_blacklist, None)
        self.assertEqual(self.t.can_build_branch("master"), True)
        self.assertEqual(
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
