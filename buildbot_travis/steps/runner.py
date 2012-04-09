import os, re

from twisted.internet import defer
from buildbot.process import buildstep
from buildbot.status.results import SUCCESS, FAILURE


class TravisRunner(buildstep.LoggingBuildStep):

    haltOnFailure = True
    flunkOnFailure = True

    progressMetrics = ShellCommand.progressMetrics + ('commands',)

    def __init__(self, **kwargs):
        kwargs.setdefault('name', step)
        kwargs.setdefault(['description', step)
        buildstep.LoggingBuildStep.__init__(self, **kwargs)

        self.addFactoryArguments(
            step = step,
            )

    @defer.inlineCallbacks
    def start(self):
        # Get components
        stdioLog = self.addLog("stdio")
        cmd = buildstep.RemoteShellCommand(workdir="build",
        command=["get", "components"],
        collectStdout=True)
        cmd.useLog(stdioLog, False)
        yield self.runCommand(cmd)
        if cmd.rc != 0:
            raise buildstep.BuildStepFailed()
        components = cmd.stdout.splitlines()

        for i, command in enumerate(components):
            self.setProgress("commands", i+1)

            stdioLog = self.addLog(component + " log")
            cmd = buildstep.RemoteShellCommand(workdir="build",command=["test", component])
            self.setupEnvironment(cmd)
            cmd.useLog(stdioLog, False)
            yield self.runCommand(cmd)
            if cmd.rc != 0:
                self.finished(FAILURE)

        self.step_status.setStatistic('commands', i)
        
        self.finished(SUCCESS)
        defer.returnValue(None)

    def setupEnvironment(self, cmd):
        """ Turn all build properties into environment variables """
        env = {}
        for k, v in self.build.getProperties().properties.items():
            env[str(k)] = str(v[0])
        cmd.args['env'].update(env)

    def describe(self, done=False):
        description = LoggingBuildStep.describe(self, done)
        if done:
            description.append('%d commands' % self.step_status.getStatistic('commands', 0))
        return description

    def hideStepIf(self, results, _):
	"""
        Check to see how many commands were run - if we didnt running any
        then hide this step
        """
        return int(self.step_status.getStatistic('commands', 0)) == 0

