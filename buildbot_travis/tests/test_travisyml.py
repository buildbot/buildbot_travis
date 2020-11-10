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
        self.t.config = {'language': 'python'}
        self.t.load_cfgdict_options()
        self.t.parse_language()


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
            - !CMake [ "target ]
        """)

    def test_yaml_not_polluted(self):
        """yaml.load should not recognise Interpolate contruct"""
        self.assertRaises(yaml.constructor.ConstructorError, yaml.safe_load, """
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
            self.t.matrix, [dict(python="2.7", env=dict(FOO='1', BAR='2'),
                                 os='linux', dist='precise', language='python'), ])

    def test_singlestringvalueenv(self):
        self.t.config["env"] = "FOO=1 BAR='2' COOKIE=\"3\""
        self.t.parse_envs()
        self.assertEqual(self.t.environments, [dict(FOO='1', BAR='2', COOKIE='3')])

        self.t.parse_matrix()
        self.assertEqual(
            self.t.matrix, [dict(python="python2.6", env=dict(FOO='1', BAR='2', COOKIE='3')), ])

    def test_singlespacevalueenv(self):
        self.t.config["env"] = "FOO=1 BAR='2 3'"
        self.t.parse_envs()
        self.assertEqual(self.t.environments, [dict(FOO='1', BAR='2 3')])

        self.t.parse_matrix()
        self.assertEqual(
            self.t.matrix, [dict(python="python2.6", env=dict(FOO='1', BAR='2 3')), ])

    def test_multienv(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        self.t.parse_envs()
        self.assertEqual(
            self.t.environments, [dict(FOO='1', BAR='2'), dict(FOO='2', BAR='1')])

        self.t.parse_matrix()
        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOO='1', BAR='2'), os='linux',
                 dist='precise', language='python'),
            dict(python="2.7", env=dict(FOO='2', BAR='1'), os='linux',
                 dist='precise', language='python'),
        ])

    def test_globalenv(self):
        self.t.config["env"] = {'global': ["FOOBAR=0"], 'matrix': ["FOO=1 BAR=2", "FOO=2 BAR=1"]}
        self.t.parse_envs()
        self.assertEqual(
            self.t.environments, [dict(FOOBAR='0', FOO='1', BAR='2'), dict(FOOBAR='0', FOO='2', BAR='1')])

        self.t.parse_matrix()
        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOOBAR='0', FOO='1', BAR='2'),
                 os='linux', dist='precise', language='python'),
            dict(python="2.7", env=dict(FOOBAR='0', FOO='2', BAR='1'),
                 os='linux', dist='precise', language='python'),
        ])

    def test_emptymatrixlenv(self):
        self.t.config["env"] = {'global': ["FOOBAR=0"]}
        self.t.parse_envs()
        self.assertEqual(
            self.t.environments, [dict(FOOBAR='0')])

        self.t.parse_matrix()
        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOOBAR='0'), os='linux',
                 dist='precise', language='python'),
        ])


class TestBuildMatrix(TravisYmlTestCase):

    def test_default_language(self):
        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(language='python', python="2.7"),
        ])

    def test_default_multiple_options(self):
        self.t.config["python"] = ['2.7', '3.5']
        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(language='python', python="2.7"),
            dict(language='python', python="3.5"),
        ])

    def test_language_with_dict(self):
        self.t.default_matrix = {
            'language': {
                'c': {'compiler': 'gcc'}
            }
        }
        self.t.language = "c"
        self.t.config["language"] = "c"

        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(compiler='gcc', language='c'),
        ])

        # Now try again with multiple compilers to use.
        self.t.config["compiler"] = ["gcc", "clang", "cc"]

        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(compiler='gcc', language='c'),
            dict(compiler='clang', language='c'),
            dict(compiler='cc', language='c'),
        ])

    def test_language_multiple_options(self):
        self.t.default_matrix = {
            'language': {
                'ruby': {
                    'gemfile': 'Gemfile',
                    'jdk': 'openjdk7',
                    'rvm': '2.2',
                }
            }
        }
        self.t.language = "ruby"
        self.t.config["language"] = "ruby"

        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(gemfile='Gemfile', jdk='openjdk7', rvm='2.2', language='ruby'),
        ])

        # Start exploding the matrix
        self.t.config["gemfile"] = ['Gemfile', 'gemfiles/a']

        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(gemfile='Gemfile', jdk='openjdk7', rvm='2.2', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='openjdk7', rvm='2.2', language='ruby'),
        ])

        self.t.config["rvm"] = ['2.2', 'jruby']

        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(gemfile='Gemfile', jdk='openjdk7', rvm='2.2', language='ruby'),
            dict(gemfile='Gemfile', jdk='openjdk7', rvm='jruby', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='openjdk7', rvm='2.2', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='openjdk7', rvm='jruby', language='ruby'),
        ])

        self.t.config["jdk"] = ['openjdk7', 'oraclejdk7']

        matrix = self.t._build_matrix()

        self.failUnlessEqual(matrix, [
            dict(gemfile='Gemfile', jdk='openjdk7', rvm='2.2', language='ruby'),
            dict(gemfile='Gemfile', jdk='openjdk7', rvm='jruby', language='ruby'),
            dict(gemfile='Gemfile', jdk='oraclejdk7', rvm='2.2', language='ruby'),
            dict(gemfile='Gemfile', jdk='oraclejdk7', rvm='jruby', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='openjdk7', rvm='2.2', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='openjdk7', rvm='jruby', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='oraclejdk7', rvm='2.2', language='ruby'),
            dict(gemfile='gemfiles/a', jdk='oraclejdk7', rvm='jruby', language='ruby'),
        ])


class TestOsMatrix(TravisYmlTestCase):

    def test_os_matrix(self):
        build_matrix = [dict(language='python', python='2.7')]

        matrix = self.t._os_matrix(build_matrix)

        self.failUnlessEqual(matrix, [
            dict(os='linux', dist='precise', language='python', python='2.7')
        ])

    def test_multiple_dists(self):
        build_matrix = [dict(language='python', python='2.7')]
        self.t.config["dist"] = ["precise", "trusty", "xenial"]

        matrix = self.t._os_matrix(build_matrix)

        self.failUnlessEqual(matrix, [
            dict(os='linux', dist='precise', language='python', python='2.7'),
            dict(os='linux', dist='trusty', language='python', python='2.7'),
            dict(os='linux', dist='xenial', language='python', python='2.7'),
        ])


class TestMatrix(TravisYmlTestCase):

    def test_exclude_match(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="2.7", env="FOO=2 BAR=1")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOO='1', BAR='2'), os='linux',
                 dist='precise', language='python'),
        ])

    def test_exclude_subset_match(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1 SPAM=3"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="2.7", env="FOO=2 BAR=1")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOO='1', BAR='2'), os='linux',
                 dist='precise', language='python'),
        ])

    def test_exclude_nomatch(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['exclude'] = [dict(python="2.7", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOO='1', BAR='2'), os='linux',
                 dist='precise', language='python'),
            dict(python="2.7", env=dict(FOO='2', BAR='1'), os='linux',
                 dist='precise', language='python'),
        ])

    def test_include(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        m = self.t.config["matrix"] = {}
        m['include'] = [dict(python="2.7", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOO='1', BAR='2'), os='linux',
                 dist='precise', language='python'),
            dict(python="2.7", env=dict(FOO='2', BAR='1'), os='linux',
                 dist='precise', language='python'),
            dict(python="2.7", env=dict(FOO='2', BAR='3')),
        ])

    def test_include_with_global(self):
        self.t.config["env"] = {'global': "CI=true", 'matrix': ["FOO=1 BAR=2", "FOO=2 BAR=1"]}
        m = self.t.config["matrix"] = {}
        m['include'] = [dict(python="2.7", env="FOO=2 BAR=3")]

        self.t.parse_envs()
        self.t.parse_matrix()

        self.assertEqual(self.t.matrix, [
            dict(python="2.7", env=dict(FOO='1', BAR='2', CI='true'),
                 os='linux', dist='precise', language='python'),
            dict(python="2.7", env=dict(FOO='2', BAR='1', CI='true'),
                 os='linux', dist='precise', language='python'),
            dict(python="2.7", env=dict(FOO='2', BAR='3', CI='true')),
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
