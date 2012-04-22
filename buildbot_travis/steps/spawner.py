
from buildbot.process import buildstep
from buildbot.process.buildstep import LoggingBuildStep, SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from twisted.spread import pb
from twisted.internet import defer
from twisted.python import log
import StringIO

from .base import ConfigurableStep

class TravisTrigger(ConfigurableStep):

    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, scheduler, **kwargs):
        if not "name" in kwargs:
            kwargs['name'] = 'trigger'
        #if not "description" in kwargs:
        #    kwargs['description'] = kwargs['name']
        LoggingBuildStep.__init__(self, **kwargs)
        self.addFactoryArguments(scheduler=scheduler)

        self.scheduler = scheduler
        self.running = False
        self.ended = False

    def interrupt(self, reason):
        if self.running and not self.ended:
            self.step_status.setText(["interrupted"])
            return self.end(EXCEPTION)

    def end(self, result):
        if not self.ended:
            self.ended = True
            return self.finished(result)

    @defer.inlineCallbacks
    def start(self):
        config = yield self.getStepConfig()

        ss = self.build.getSourceStamp()
        got = self.build.getProperty('got_revision')
        if got:
            ss = ss.getAbsoluteSourceStamp(got)

        # Stop the build early if .travis.yml says we should ignore branch
        if ss.branch and not config.can_build_branch(ss.branch):
            defer.returnValue(self.end(SUCCESS))

        # Find the master object
        master = self.build.builder.botmaster.parent

        # Find the scheduler we are going to use to queue actual builds
        all_schedulers = self.build.builder.botmaster.parent.allSchedulers()
        all_schedulers = dict([(sch.name, sch) for sch in all_schedulers])
        sch = all_schedulers[self.scheduler]

        triggered = []

        self.running = True

        for env in config.environments:
            props_to_set = Properties()
            props_to_set.updateFromProperties(self.build.getProperties())
            props_to_set.update(env, ".travis.yml")
            props_to_set.setProperty("spawned_by",  self.build.build_status.number, "Scheduler")

            ss_setid = yield ss.getSourceStampSetId(master)
            triggered.append(sch.trigger(ss_setid, set_props=props_to_set))

        results = yield defer.DeferredList(triggered, consumeErrors=1)

        was_exception = was_failure = False
        brids = {}

        for was_cb, results in results:
            if isinstance(results, tuple):
                results, some_brids = results
                brids.update(some_brids)

            if not was_cb:
                was_exception = True
                log.err(results)
                continue

            if results == FAILURE:
                was_failure = True

        if was_exception:
            result = EXCEPTION
        elif was_failure:
            result = FAILURE
        else:
            result = SUCCESS

        if brids:
            brid_to_bn = dict((_brid,_bn) for _bn,_brid in brids.iteritems())
            res = yield defer.DeferredList([master.db.builds.getBuildsForRequest(br) for br in brids.values()], consumeErrors=1)
            for was_cb, builddicts in res:
                if was_cb:
                    for build in builddicts:
                        bn = brid_to_bn[build['brid']]
                        num = build['number']

                        url = master.status.getURLForBuild(bn, num)
                        self.step_status.addURL("%s #%d" % (bn,num), url)

        defer.returnValue(self.end(result))

