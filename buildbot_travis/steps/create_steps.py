# Copyright 2012-2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

import os
import re
import textwrap
import traceback

from twisted.internet import defer

from buildbot.process.buildstep import SUCCESS, BuildStep, ShellMixin
from buildbot.process import logobserver
from buildbot.steps import shell

from ..travisyml import TRAVIS_HOOKS
from .base import ConfigurableStep


class SetupVirtualEnv(ShellMixin, BuildStep):
    name = "setup virtualenv"
    sandboxname = "sandbox"

    def __init__(self, python, **kwargs):
        self.python = python
        super(SetupVirtualEnv, self).__init__(haltOnFailure=True, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        command = self.buildCommand()
        cmd = yield self.makeRemoteShellCommand(
            command=["bash", "-c", command])
        yield self.runCommand(cmd)
        self.setProperty(
            "PATH", os.path.join(
                self.getProperty("builddir"), self.workdir, "sandbox/bin") + ":" +
            self.worker.worker_environ['PATH'])
        defer.returnValue(cmd.results())

    def buildCommand(self):
        # set up self.command as a very long sh -c invocation
        command = textwrap.dedent("""\
        PYTHON='python{virtualenv_python}'
        VE='{sandboxname}'
        VEPYTHON='{sandboxname}/bin/python'

        # first, set up the virtualenv if it hasn't already been done, or if it's
        # broken (as sometimes happens when a slave's Python is updated)
        if ! test -f "$VE/bin/pip" || ! test -d "$VE/lib/$PYTHON" || ! "$VE/bin/python" -c 'import math'; then
            echo "Setting up virtualenv $VE";
            rm -rf "$VE";
            test -d "$VE" && {{ echo "$VE couldn't be removed"; exit 1; }};
            virtualenv -p $PYTHON "$VE" || exit 1;
        else
            echo "Virtualenv already exists"
        fi

        echo "Upgrading pip";
        $VE/bin/pip install -U pip

        """).format(
            virtualenv_python=self.python, sandboxname=self.sandboxname)
        return command


class ShellCommand(shell.ShellCommand):

    flunkOnFailure = True
    haltOnFailure = True
    warnOnWarnings = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addLogObserver('stdio', logobserver.LineConsumerLogObserver(self.log_line_consumer))
        self.total_count = 0
        self.skipped_count = 0
        self.fails_count = 0
        self.errors_count = 0
        self.has_tests = False

    @defer.inlineCallbacks
    def run(self):
        env = getattr(self, 'env', {})
        for k, v in self.build.getProperties().properties.items():
            env[str(k)] = str(v[0])
        self.env = env

        cmd = yield self.makeRemoteShellCommand()
        yield self.runCommand(cmd)

        if self.total_count > 0:
            # We work out passed at the end because most test runners dont tell us
            # and we can't distinguish between different test systems easily so we
            # might double count.
            passed = self.total_count - (self.skipped_count + self.fails_count + self.errors_count)

            self.setStatistic('total', self.total_count)
            self.setStatistic('fails', self.fails_count)
            self.setStatistic('errors', self.errors_count)
            self.setStatistic('skipped', self.skipped_count)
            self.setStatistic('passed', passed)

        return cmd.results()

    def log_line_consumer(self):
        while True:
            stream, line = yield
            if stream not in 'oe':
                continue

            outputs = re.findall(
                r"Ran (?P<count>[\d]+) tests with (?P<fail>[\d]+) failures and (?P<error>[\d]+) errors",
                line)
            for output in outputs:
                self.total_count += int(output[0])
                self.fails_count += int(output[1])
                self.errors_count += int(output[2])

            # Twisted
            # Example::
            #    FAILED (errors=5, successes=11)
            #    PASSED (successes=16)
            if line.startswith("FAILED (") or line.startswith("PASSED ("):
                line = line[8:][:-1]
                stats = line.split(", ")

                for stat in stats:
                    k, v = stat.split("=")
                    try:
                        v = int(v)
                        if k == 'successes':
                            self.total_count += v
                        elif k == 'failures':
                            self.total_count += v
                            self.fails_count += v
                        elif k == 'errors':
                            self.total_count += v
                            self.errors_count += v
                        elif k == 'skips':
                            self.total_count += v
                            self.skipped_count += v
                    except ValueError:
                        pass

            # This matches Nose and Django output
            # Example::
            #     Ran 424 tests in 152.927s
            #     FAILED (failures=1)
            #     FAILED (errors=3)
            if 'FAIL:' in line:
                self.fails_count += 1
            if 'ERROR:' in line:
                self.errors_count += 1
            for number in re.findall(r"Ran (?P<count>[\d]+)", line):
                self.total_count += int(number)

    def getResultSummary(self):
        description = super().getResultSummary()

        if self.hasStatistic('total'):

            def append(stat, fmtstring):
                val = self.getStatistic(stat, 0)
                if val:
                    description.append(fmtstring % val)

            append("total", "%d tests")
            append("fails", "%d fails")
            append("errors", "%d errors")
            append("skipped", "%d skipped")
            append("passed", "%d passed")

        return description


class TravisSetupSteps(ConfigurableStep):

    name = "setup-steps"
    haltOnFailure = True
    flunkOnFailure = True
    MAX_NAME_LENGTH = 47
    disable = False

    def addSetupVirtualEnv(self, python):
        step = SetupVirtualEnv(python, doStepIf=not self.disable)
        self.build.addStepsAfterLastStep([step])

    def addBBTravisStep(self, command):
        name = None
        condition = None
        shell = None
        step = None
        original_command = command
        if isinstance(command, dict):
            name = command.get("title")
            shell = command.get("shell", shell)
            condition = command.get("condition")
            step = command.get("step")
            command = command.get("cmd")

        if isinstance(command, BuildStep):
            step = command

        if condition is not None:
            try:
                if not self.testCondition(condition):
                    return
            except Exception:
                self.descriptionDone = u"Problem parsing condition"
                self.addCompleteLog("condition error", traceback.format_exc())
                return

        if step is None:
            if command is None:
                self.addCompleteLog("bbtravis.yml error",
                                    "Neither step nor cmd is defined: %r" %
                                    (original_command, ))
                return
            if name is None:
                name = self.truncateName(command)

            if shell is not None:
                # The following is dicy, as it assumes that all shells use
                # -c to take a command string.  This is not always the case,
                # such as for Windows cmd, and in that case, a command list
                # is needed.
                if not isinstance(shell, list):
                    shell = [ shell, '-c' ]
                command = list(shell) + list(command)
            step = ShellCommand(
                name=name, description=command, command=command, doStepIf=not self.disable)
        self.build.addStepsAfterLastStep([step])

    def testCondition(self, condition):
        l = dict(
            (k, v)
            for k, (v, s) in self.build.getProperties().properties.items())
        return eval(condition, l)

    def truncateName(self, name):
        name = name.lstrip("#")
        name = name.lstrip(" ")
        name = name.split("\n")[0]
        if len(name) > self.MAX_NAME_LENGTH:
            name = name[:self.MAX_NAME_LENGTH - 3] + "..."
        return name

    @defer.inlineCallbacks
    def run(self):
        config = yield self.getStepConfig()
        if 'python' in config.language:
            self.addSetupVirtualEnv(self.getProperty("python"))
        for k in TRAVIS_HOOKS:
            for command in getattr(config, k):
                self.addBBTravisStep(command=command)

        defer.returnValue(SUCCESS)
