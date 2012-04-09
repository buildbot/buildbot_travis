
from twisted.trial import unittest

from buildbot.test.util import steps
from buildbot.test.fake.remotecommand import ExpectShell

from buildbot_travis.steps import TravisRunner


class TestTravisRunner(steps.BuildStepMixin, unittest.TestCase):
    def setUp(self):
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def test_MultiComponent(self):
        self.setupStep(TravisRunner("install"))
        self.expectCommands(
            ExpectShell(workdir="build", command=["get", "components"])
          + ExpectShell.log('stdio', stdout='one\ntwo\n')
          + 0,
            ExpectShell(workdir="build", command=["test", "one"])
          + ExpectShell.log('one log', stdout='one')
          + 0,
            ExpectShell(workdir="build", command=["test", "two"])
          + ExpectShell.log('two log', stdout='one')
          + 0
        )
        self.expectOutcome(result=SUCCESS, status_text=["generic"])
        return self.runStep()

