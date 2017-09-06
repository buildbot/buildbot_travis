from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import textwrap

from twisted.trial import unittest

from buildbot.plugins import util, worker
from buildbot.test.util import config
from buildbot_travis.configurator import TravisConfigurator


class TravisConfiguratorTestCase(unittest.TestCase, config.ConfigErrorsMixin):
    def setUp(self):
        self.c = TravisConfigurator({'www': {}}, "")

    def test_auth_no_conf(self):
        self.c.cfgdict = {
        }
        self.c.createAuthConfig()

    def test_auth_no_conf_type(self):
        self.c.cfgdict = {
            'auth': {
            }
        }
        self.c.createAuthConfig()

    def test_auth_badtype(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'foo'
            }
        }
        self.assertRaisesConfigError("auth type foo is not supported",
                                     self.c.createAuthConfig)

    def test_auth_github_noargs(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitHub'
            }
        }
        self.assertRaisesConfigError("auth requires parameter clientid but only has {'type': 'GitHub'}",
                                     self.c.createAuthConfig)

    def test_auth_github(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitHub',
                'clientid': 'foo',
                'clientsecret': 'bar'
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['auth'], util.GitHubAuth)

    def test_auth_bitbucket(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'Bitbucket',
                'clientid': 'foo',
                'clientsecret': 'bar'
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['auth'], util.BitbucketAuth)

    def test_auth_google(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'Google',
                'clientid': 'foo',
                'clientsecret': 'bar'
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['auth'], util.GoogleAuth)

    def test_auth_gitlab_no_url(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitLab',
                'clientid': 'foo',
                'clientsecret': 'bar'
            }
        }
        self.assertRaisesConfigError("auth requires parameter instanceUri but only has",
                                     self.c.createAuthConfig)

    def test_auth_gitlab(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitLab',
                'clientid': 'foo',
                'clientsecret': 'bar',
                'instanceUri': 'http://sd'
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['auth'], util.GitLabAuth)

    def test_auth_custom(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'Custom',
                'customcode': textwrap.dedent("""
                    from buildbot.plugins import *
                    auth = util.UserPasswordAuth({"homer": "doh!"})
                """)
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['auth'], util.UserPasswordAuth)

    def test_auth_custom_noauth(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'Custom',
                'customcode': textwrap.dedent("""
                    from buildbot.plugins import *
                    foo = util.UserPasswordAuth({"homer": "doh!"})
                """)
            }
        }
        self.assertRaisesConfigError("custom code does not generate variable auth",
                                     self.c.createAuthConfig)

    def test_authz_custom(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitHub',
                'clientid': 'foo',
                'clientsecret': 'bar',
                'authztype': 'Custom',
                'customauthzcode': textwrap.dedent("""
                    from buildbot.plugins import *
                    allowRules=[
                        util.StopBuildEndpointMatcher(role="admins"),
                        util.ForceBuildEndpointMatcher(role="admins"),
                        util.RebuildBuildEndpointMatcher(role="admins")
                    ]
                    roleMatchers=[
                        util.RolesFromEmails(admins=["my@email.com"])
                    ]
                """)
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['authz'], util.Authz)

    def test_authz_groups(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitHub',
                'clientid': 'foo',
                'clientsecret': 'bar',
                'authztype': 'Groups',
                'groups': ['buildbot']
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['authz'], util.Authz)

    def test_authz_emails(self):
        self.c.cfgdict = {
            'auth': {
                'type': 'GitHub',
                'clientid': 'foo',
                'clientsecret': 'bar',
                'authztype': 'Emails',
                'emails': ['buildbot@buildbot.net']
            }
        }
        self.c.createAuthConfig()
        self.assertIsInstance(self.c.config['www']['authz'], util.Authz)

    def test_worker_worker(self):
        self.c.cfgdict = {
            'workers': [{
                'type': 'Worker',
                'name': 'foo',
                'password': 'bar',
                'number': 1
            }]
        }
        self.c.createWorkerConfig()
        self.assertIsInstance(self.c.config['workers'][0], worker.Worker)
        self.assertEqual(self.c.config['workers'][0].name, 'foo')

    def test_worker_2worker(self):
        self.c.cfgdict = {
            'workers': [{
                'type': 'Worker',
                'name': 'foo',
                'password': 'bar',
                'number': 2
            }]
        }
        self.c.createWorkerConfig()
        self.assertIsInstance(self.c.config['workers'][0], worker.Worker)
        self.assertIsInstance(self.c.config['workers'][1], worker.Worker)
        self.assertEqual(self.c.config['workers'][0].name, 'foo_1')
        self.assertEqual(self.c.config['workers'][1].name, 'foo_2')
        self.assertEqual(len(self.c.config['workers']), 2)

    def test_worker_localworker(self):
        self.c.cfgdict = {
            'workers': [{
                'type': 'LocalWorker',
                'name': 'foo',
                'number': 1
            }]
        }
        self.c.createWorkerConfig()
        self.assertIsInstance(self.c.config['workers'][0], worker.LocalWorker)
        self.assertEqual(self.c.config['workers'][0].name, 'foo')

    def test_worker_dockerworker(self):
        self.c.cfgdict = {
            'workers': [{
                'type': 'DockerWorker',
                'name': 'foo',
                'number': 10,
                'docker_host': 'tcp://foo:2193',
                'volumes': '/foo:/foo, /bar:/bar',
                'image': 'slave'
            }]
        }
        self.c.createWorkerConfig()
        self.assertIsInstance(self.c.config['workers'][0], worker.DockerLatentWorker)
        self.assertEqual(self.c.config['workers'][0].name, 'foo_1')
        self.assertEqual(len(self.c.config['workers']), 10)
        self.assertEqual(
            self.c.config['workers'][0].getConfigDict()['kwargs']['volumes'],
            ['/foo:/foo', '/bar:/bar'])
