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
from buildbot.steps.slave import CompositeStepMixin
from twisted.internet import defer

from ..travisyml import TravisYml


class ConfigurableStepMixin(CompositeStepMixin):

    """
    Base class for a step which can be tuned by changing settings in .travis.yml
    """

    def getResultSummary(self):
        if self.descriptionDone is not None:
            return {u'step': self.descriptionDone}
        else:
            super(ConfigurableStepMixin, self).getResultSummary()

    @defer.inlineCallbacks
    def getStepConfig(self):
        try:
            travis_yml = yield self.getFileContentFromSlave(".travis.yml", abandonOnFailure=True)
        except buildstep.BuildStepFailed:
                self.descriptionDone = u"unable to fetch .travis.yml"
                raise
        self.addCompleteLog(".travis.yml", travis_yml)

        config = TravisYml()
        config.parse(travis_yml)

        defer.returnValue(config)


class ConfigurableStep(buildstep.LoggingBuildStep, ConfigurableStepMixin):
    pass
