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
        log = self.addLog(".travis.yml")
        cmd = self.cmd = buildstep.RemoteShellCommand(workdir="build", command=["cat", ".travis.yml"])
        cmd.useLog(log, False, "stdio")
        yield self.runCommand(cmd)
        self.cmd = None
        if cmd.rc != 0:
            raise buildstep.BuildStepFailed()

        config = TravisYml()
        config.parse(log.getText())

        defer.returnValue(config)
