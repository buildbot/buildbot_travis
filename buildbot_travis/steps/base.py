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
        config = TravisYml()

        struct = self.build.getProperty(".travis.yml", None)
        if struct:
            config.parse(struct)
            defer.returnValue(config)
             
        log = self.addLog(".travis.yml")
        cmd = self.cmd = buildstep.RemoteShellCommand(workdir="build", command=["cat", ".travis.yml"])
        cmd.useLog(log, False, "stdio")
        yield self.runCommand(cmd)
        self.cmd = None
        if cmd.rc != 0:
            raise buildstep.BuildStepFailed()

        config = TravisYml()
        config.parse(log.getText())

        self.build.setProperty(".travis.yml", config.config, ".VCS")

        defer.returnValue(config)

