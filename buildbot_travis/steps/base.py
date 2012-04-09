from buildbot.process import buildstep
from buildbot.process.buildstep import SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from twisted.internet import defer

from ..travisyml import TravisYml


class ConfigurableStep(buildstep.LoggingBuildStep):

    """
    Base class for a step which can be tuned by changing settings in .travis.yml
    """

    @defer.inlineCallbacks
    def getStepConfig(self):
        self.stdioLog = self.addLog("stdio")
        cmd = buildstep.RemoteShellCommand(workdir="build", command=["cat", ".travis.yml"])
        cmd.useLog(self.stdioLog, False)
        yield self.runCommand(cmd)
        if cmd.rc != 0:
            raise buildstep.BuildStepFailed()

        config = TravisYml()
        config.parse(self.stdioLog.getText())

        defer.returnValue(config)

