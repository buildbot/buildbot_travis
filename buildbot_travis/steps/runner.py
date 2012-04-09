import os, re

from buildbot.steps.transfer import FileDownload
from buildbot.steps.shell import ShellCommand
from buildbot.process.buildstep import LogLineObserver

def sibpath(path):
    return os.path.join(os.path.dirname(__file__), path)


class TravisLogLineObserver(LogLineObserver):

    _final_matcher = re.compile("==> Executed (?P<commands>\d+) commands")

    nbCommands = 0

    def outLineReceived(self, line):
        if line.startswith("==> "):
            self.nbCommands += 1
            self.step.setProgress("commands", self.nbCommands)

        # Last output looks like this:
        # ==> Executed %d commands
        r = self._final_matcher.search(line)
        if r:
            self.nbCommands = int(r.groups("commands")[0])
            self.step.setProgress("commands", self.nbCommands)


class TravisRunner(ShellCommand):

    haltOnFailure = True
    flunkOnFailure = True

    progressMetrics = ShellCommand.progressMetrics + ('commands',)

    def __init__(self, step, **kwargs):
        kwargs['name'] = step
        kwargs['description'] = step
        kwargs['command'] = "./travis-runner %s" % step

        ShellCommand.__init__(self, **kwargs)

        self.addFactoryArguments(
            step = step,
            )

    def setupEnvironment(self, cmd):
        """ Turn all build properties into environment variables """
        ShellCommand.setupEnvironment(self, cmd)

        env = {}
        for k, v in self.build.getProperties().properties.items():
            env[str(k)] = str(v[0])

        cmd.args['env'].update(env)

    def setupLogfiles(self, cmd, logfiles):
        self.observer = TravisLogLineObserver()
        self.addLogObserver('stdio', self.observer)
        ShellCommand.setupLogfiles(self, cmd, logfiles)

    def describe(self, done=False):
        description = ShellCommand.describe(self, done)
        if done:
            description.append('%d commands' % self.step_status.getStatistic('commands', 0))
        return description

    def createSummary(self, log):
        self.step_status.setStatistic('commands', self.observer.nbCommands)

    def hideStepIf(self, results, _):
	"""
        Check to see how many commands were run - if we didnt running any
        then hide this step
        """
        return int(self.step_status.getStatistic('commands', 0)) == 0









