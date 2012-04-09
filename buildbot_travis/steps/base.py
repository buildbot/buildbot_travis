from buildbot.process import buildstep
from buildbot.process.buildstep import SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from twisted.internet import defer

class ConfigurableStep(buildstep.LoggingBuildStep):

    """
    Base class for a step which can be tuned by changing settings in .travis.yml
    """

    @defer.inlineCallback
    def getStepConfig(self):
        log = self.addLog("get .travis.yml")
        cmd = buildstep.RemoteShellCommand(workdir="build", command=["cat", ".travis.yml"], collectStdout=True)
        cmd.useLog(log, False)
        yield self.runCommand(cmd)
        if cmd.rc != 0:
            raise buildstep.BuildStepFailed()

        config = TravisYml()
        config.parse(cmd.stdout)

        defer.returnValue(config)

