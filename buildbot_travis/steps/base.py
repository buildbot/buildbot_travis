# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2012-2103 Isotoma Limited

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
