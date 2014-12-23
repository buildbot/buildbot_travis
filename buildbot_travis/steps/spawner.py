
from buildbot.process import buildstep
from buildbot.process.buildstep import LoggingBuildStep, SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from buildbot.steps.trigger import Trigger
from twisted.spread import pb
from twisted.internet import defer
from twisted.python import log
import StringIO

from .base import ConfigurableStepMixin


class TravisTrigger(Trigger, ConfigurableStepMixin):

    haltOnFailure = True
    flunkOnFailure = True

    sourceStamps = []
    alwaysUseLatest = False
    updateSourceStamp = True

    def __init__(self, scheduler, **kwargs):
        if "name" not in kwargs:
            kwargs['name'] = 'trigger'
        Trigger.__init__(self, waitForFinish=True, schedulerNames=[scheduler], **kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.config = yield self.getStepConfig()

        rv = yield Trigger.run(self)
        defer.returnValue(rv)

    def getSchedulers(self):
        (triggered_schedulers, invalid_schedulers) = Trigger.getSchedulers(self)
        # baseclass should return one scheduler
        if invalid_schedulers:
            return ([], invalid_schedulers)

        sch = triggered_schedulers[0]
        triggered_schedulers = []

        for env in self.config.matrix:
            props_to_set = Properties()
            props_to_set.updateFromProperties(self.build.getProperties())
            props_to_set.update(env["env"], ".travis.yml")
            props_to_set.setProperty("spawned_by",  self.build.number, "Scheduler")

            triggered_schedulers.append((sch, props_to_set))
        return triggered_schedulers, []
