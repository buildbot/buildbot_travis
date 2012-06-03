import re

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

    def createSummary(self, stdio):
        self.updateStats(stdio)

    def updateStats(self, log):
        """
        Parse test results out of common test harnesses.

        Currently supported are:

         * Plone
         * Nose
         * Trial
         * Something mitchell wrote in Java
        """
        stdio = log.getText()

        total = passed = skipped = fails = warnings = errors = 0
        hastests = False


        # Plone? That has lines starting "Ran" and "Total". Total is missing if there is only a single layer.
        # For this reason, we total ourselves which lets us work even if someone runes 2 batches of plone tests
        # from a single target

        # Example::
        #     Ran 24 tests with 0 failures and 0 errors in 0.009 seconds

        if not hastests:
            outputs = re.findall("Ran (?P<count>[\d]+) tests with (?P<fail>[\d]+) failures and (?P<error>[\d]+) errors", stdio)
            for output in outputs:
                total += int(output[0])
                fails += int(output[1])
                errors += int(output[2])
                hastests = True


        # Twisted

        # Example::
        #    FAILED (errors=5, successes=11)
        #    PASSED (successes=16)
        if not hastests:
            for line in stdio.split("\n"):
                if line.startswith("FAILED (") or line.startswith("PASSED ("):
                    hastests = True

                    line = line[8:][:-1]
                    stats = line.split(", ")
                    data = {}

                    for stat in stats:
                        k, v = stat.split("=")
                        data[k] = int(v)

                    if not "successes" in data:
                        total = 0
                        for number in re.findall("Ran (?P<count>[\d]+) tests in ", stdio):
                            total += int(number)
                        data["successes"] = total - sum(data.values())

        # This matches Nose and Django output

        # Example::
        #     Ran 424 tests in 152.927s
        #     FAILED (failures=1)
        #     FAILED (errors=3)

        if not hastests:
            fails += len(re.findall('FAIL:', stdio))
            errors += len(re.findall('======================================================================\nERROR:', stdio))
            for number in re.findall("Ran (?P<count>[\d]+)", stdio):
                total += int(number)
                hastests = True


	# We work out passed at the end because most test runners dont tell us
	# and we can't distinguish between different test systems easily so we
	# might double count.
        passed = total - (skipped + fails + errors + warnings)

        # Update the step statistics with out shiny new totals
        if hastests:
            self.step_status.setStatistic('total', total)
            self.step_status.setStatistic('fails', fails)
            self.step_status.setStatistic('errors', errors)
            self.step_status.setStatistic('warnings', warnings)
            self.step_status.setStatistic('skipped', skipped)
            self.step_status.setStatistic('passed', passed)

    def describe(self, done=False):
        description = shell.ShellCommand.describe(self, done)

        if done and self.step_status.hasStatistic('total'):
            def append(stat, fmtstring):
                val = self.step_status.getStatistic(stat, 0)
                if val:
                    description.append(fmtstring % val)

            append("total", "%d tests")
            append("fails", "%d fails")
            append("errors", "%d errors")
            append("warnings", "%d warnings")
            append("skipped", "%d skipped")
            append("passed", "%d passed")

        return description


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

