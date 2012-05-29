from twisted.internet import defer
from twisted.python import log
from buildbot.process import buildstep
from buildbot.process.buildstep import SUCCESS, FAILURE
from buildbot.steps import shell

from .base import ConfigurableStep
from ..travisyml import TRAVIS_HOOKS


class ShellCommand(shell.ShellCommand):

    flunkOnFailure = True
    haltOnFailure = True
    warnOnWarnings = True

    def setupEnvironment(self, cmd):
        """ Turn all build properties into environment variables """
        shell.ShellCommand.setupEnvironment(self, cmd)
        env = {}
        for k, v in self.build.getProperties().properties.items():
            env[str(k)] = str(v[0])
        cmd.args['env'].update(env)


class TravisSetupSteps(ConfigurableStep):

    name = "setup-steps"
    haltOnFailure = True
    flunkOnFailure = True
    workdir = ''

    def setDefaultWorkdir(self, workdir):
        ConfigurableStep.setDefaultWorkdir(self, workdir)
        self.workdir = workdir

    def addShellCommand(self, name, command):
        b = self.build
        
        step = ShellCommand(
            name = name,
            description = command,
            command = ['/bin/bash', '-c', command],
            )

        step.setBuild(b)
        step.setBuildSlave(b.slavebuilder.slave)
        step.setDefaultWorkdir(self.workdir)
        b.steps.append(step)

        step_status = b.build_status.addStepWithName(step.name)
        step.setStepStatus(step_status)

        # TODO: Workout BuildProgress / expectations stuff

    @defer.inlineCallbacks
    def start(self):
        config = yield self.getStepConfig()

        for k in TRAVIS_HOOKS:
            for i, command in enumerate(getattr(config, k)):
                self.addShellCommand(
                    name = "travis_"+k+str(i),
                    command = command,
                    )

        self.finished(SUCCESS)
        defer.returnValue(None)

