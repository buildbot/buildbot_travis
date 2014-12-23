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

    @defer.inlineCallbacks
    def getStepConfig(self):
        travis_yml = yield self.getFileContentFromSlave(".travis.yml", abandonOnFailure=True)
        self.addCompleteLog(".travis.yml", travis_yml)

        config = TravisYml()
        config.parse(travis_yml)

        defer.returnValue(config)


class ConfigurableStep(buildstep.LoggingBuildStep, ConfigurableStepMixin):
    pass
