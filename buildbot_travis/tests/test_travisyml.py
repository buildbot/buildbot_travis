from twisted.trial import unittest

from buildbot_travis.travisyml import TravisYml

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

    def test_multienv(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        self.t.parse_envs()
        self.failUnlessEqual(self.t.environments, [dict(FOO='1', BAR='2'), dict(FOO='2', BAR='1')])


class TestBranches(TravisYmlTestCase):

    def test_nobranches(self):
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, None)
        self.failUnlessEqual(self.t.branch_blacklist, None)
        self.failUnlessEqual(self.t.can_build_branch("master"), True)

    def test_whitelist(self):
        b = self.t.config["branches"] = {"only": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, ["master"])
        self.failUnlessEqual(self.t.branch_blacklist, None)
        self.failUnlessEqual(self.t.can_build_branch("master"), True)
        self.failUnlessEqual(self.t.can_build_branch("feature-new-stuff"), False)

    def test_whitelist_regex(self):
        b = self.t.config["branches"] = {"only": ['master', '/^deploy-.*$/']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.can_build_branch("master"), True)
        self.failUnlessEqual(self.t.can_build_branch("wibble"), False)
        self.failUnlessEqual(self.t.can_build_branch("deploy-cool-regex"), True)

    def test_blacklist(self):
        b = self.t.config["branches"] = {"except": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, None)
        self.failUnlessEqual(self.t.branch_blacklist, ["master"])
        self.failUnlessEqual(self.t.can_build_branch("master"), False)
        self.failUnlessEqual(self.t.can_build_branch("feature-new-stuff"), True)

    def test_whitelist_and_blacklist(self):
        """ Test that blacklist is ignored when both whitelist and blacklist are present """
        b = self.t.config["branches"] = {"only": ['master'], "except": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branch_whitelist, ["master"])
        self.failUnlessEqual(self.t.branch_blacklist, None)
        self.failUnlessEqual(self.t.can_build_branch("master"), True)
        self.failUnlessEqual(self.t.can_build_branch("feature-new-stuff"), False)

