from twisted.internet import defer
from buildbot.process import buildstep
from buildbot.status.results import SUCCESS, FAILURE

from .base import ConfigurableStep

class TravisRunner(ConfigurableStep):

    haltOnFailure = True
    flunkOnFailure = True

    progressMetrics = buildstep.ConfigurableStep.progressMetrics + ('commands',)

    def __init__(self, step, **kwargs):
        kwargs.setdefault('name', step)
        #kwargs.setdefault('description', step)
        buildstep.ConfigurableStep.__init__(self, **kwargs)

        self.addFactoryArguments(
            step = step,
            )

        self.step = step

    @defer.inlineCallbacks
    def start(self):
        config = yield self.getStepConfig()

        for i, command in enumerate(getattr(config, self.step)):
            self.setProgress("commands", i+1)

            stdioLog = self.addLog("%d.log" % i)
            cmd = buildstep.RemoteShellCommand(workdir="build",command=command)
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
        description = buildstep.ConfigurableStep.describe(self, done)
        if done:
            description.append('%d commands' % self.step_status.getStatistic('commands', 0))
        return description

    def hideStepIf(self, results, _):
	"""
        Check to see how many commands were run - if we didnt running any
        then hide this step
        """
        return int(self.step_status.getStatistic('commands', 0)) == 0

