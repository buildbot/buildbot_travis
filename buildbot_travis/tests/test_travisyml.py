import unittest

from buildbot_travis.travisyml import TravisYml

class TestTravisYml(unittest.TestCase):

    def setUp(self):
        self.t = TravisYml()
        self.t.config = {}

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

