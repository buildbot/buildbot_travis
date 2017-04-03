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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from twisted.internet import defer

from buildbot.process import buildstep
from buildbot.steps.worker import CompositeStepMixin

from ..travisyml import TravisYml, TravisYmlInvalid


HOW_TO_DEBUG = """
In order to help you debug, you can install the bbtravis tool:

virtualenv sandbox
. ./sandbox/bin/activate
pip install buildbot_travis
bbtravis run
"""


class ConfigurableStepMixin(CompositeStepMixin):

    """
    Base class for a step which can be tuned by changing settings in .travis.yml
    """
    TRAVIS_FILENAMES = [".bbtravis.yml", ".travis.yml"]

    def getResultSummary(self):
        if self.descriptionDone is not None:
            return {u'step': self.descriptionDone}
        else:
            super(ConfigurableStepMixin, self).getResultSummary()

    def addHelpLog(self):
        self.addCompleteLog("help.txt", HOW_TO_DEBUG)

    @defer.inlineCallbacks
    def getStepConfig(self):
        travis_yml = None
        for filename in self.TRAVIS_FILENAMES:
            try:
                travis_yml = yield self.getFileContentFromWorker(filename, abandonOnFailure=True)
                break
            except buildstep.BuildStepFailed as e:
                continue

        if travis_yml is None:
            self.descriptionDone = u"unable to fetch .travis.yml"
            self.addCompleteLog(
                "error",
                "Please put a file named .travis.yml at the root of your repository:\n{0}".format(e))
            self.addHelpLog()
            raise

        self.addCompleteLog(filename, travis_yml)

        config = TravisYml()
        try:
            config.parse(travis_yml)
        except TravisYmlInvalid as e:
            self.descriptionDone = u"bad .travis.yml"
            self.addCompleteLog(
                "error",
                ".travis.yml is invalid:\n{0}".format(e))
            self.addHelpLog()
            raise buildstep.BuildStepFailed("Bad travis file")
        defer.returnValue(config)


class ConfigurableStep(buildstep.LoggingBuildStep, ConfigurableStepMixin):
    pass
