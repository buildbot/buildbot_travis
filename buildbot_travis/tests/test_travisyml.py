import unittest

from buildbot_travis.travisyml import TravisYml

class TravisYmlTestCase(unittest.TestCase):

    def setUp(self):
        self.t = TravisYml()
        self.t.config = {}


class TestEnv(TravisYmlTestCase):

    def parse_noenv(self):
        self.t.parse_env()
        self.failUnlessEqual(self.t.environments, [{}])

    def parse_singleenv(self):
        self.t.config["env"] = "FOO=1 BAR=2"
        self.t.parse_env()
        self.failUnlessEqual(self.t.environments, [dict(FOO=1, BAR=2)])

    def parse_multienv(self):
        self.t.config["env"] = ["FOO=1 BAR=2", "FOO=2 BAR=1"]
        self.t.parse_env()
        self.failUnlessEqual(self.t.environments, [dict(FOO=1, BAR=2), dict(FOO=2, BAR=1)])


class TestBranches(TravisYmlTestCase):

    def parse_nobranches(self):
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branches_whitelist, None)
        self.failUnlessEqual(self.t.branches_blacklist, None)
        self.failUnlessEqual(self.can_build_branch("master"), True)

    def parse_whitelist(self):
        b = self.t.config["branches"] = {"only": []}
        b.append("master")
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branches_whitelist, ["master"])
        self.failUnlessEqual(self.t.branches_blacklist, None)
        self.failUnlessEqual(self.can_build_branch("master"), True)
        self.failUnlessEqual(self.can_build_branch("feature-new-stuff"), False)

    def parse_whitelist_regex(self):
        b = self.t.config["branches"] = {"only": ['master', '/^deploy-.*$/']}
        self.t.parse_branches()
        self.failUnlessEqual(self.can_build_branch("master"), True)
        self.failUnlessEqual(self.can_build_branch("wibble"), False)
        self.failUnlessEqual(self.can_build_branch("deploy-cool-regex"), True)

    def parse_blacklist(self):
        b = self.t.config["branches"] = {"except": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branches_whitelist, None)
        self.failUnlessEqual(self.t.branches_blacklist, ["master"])
        self.failUnlessEqual(self.can_build_branch("master"), False)
        self.failUnlessEqual(self.can_build_branch("feature-new-stuff"), True)

    def parse_whitelist_and_blacklist(self):
        """ Test that blacklist is ignored when both whitelist and blacklist are present """
        b = self.t.config["branches"] = {"only": ['master'], "except": ['master']}
        self.t.parse_branches()
        self.failUnlessEqual(self.t.branches_whitelist, ["master"])
        self.failUnlessEqual(self.t.branches_blacklist, None)
        self.failUnlessEqual(self.can_build_branch("master"), True)
        self.failUnlessEqual(self.can_build_branch("feature-new-stuff"), False)

