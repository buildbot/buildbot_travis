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

    sourceStamps = []
    alwaysUseLatest = False
    updateSourceStamp = True

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

    def prepareSourcestampListForTrigger(self):
        if self.sourceStamps:
            ss_for_trigger = {}
            for ss in self.sourceStamps:
                codebase = ss.get('codebase','')
                assert codebase not in ss_for_trigger, "codebase specified multiple times"
                ss_for_trigger[codebase] = ss
            return ss_for_trigger

        if self.alwaysUseLatest:
            return {}

        # start with the sourcestamps from current build
        ss_for_trigger = {}
        objs_from_build = self.build.getAllSourceStamps()
        for ss in objs_from_build:
            ss_for_trigger[ss.codebase] = ss.asDict()

        # overrule revision in sourcestamps with got revision
        if self.updateSourceStamp:
            got = self.build.build_status.getAllGotRevisions()
            for codebase in ss_for_trigger:
                if codebase in got:
                    ss_for_trigger[codebase]['revision'] = got[codebase]

        return ss_for_trigger

    @defer.inlineCallbacks
    def start(self):
        config = yield self.getStepConfig()

        ss_for_trigger = self.prepareSourcestampListForTrigger()
        ss = ss_for_trigger[self.build.builder.name]

        # Stop the build early if .travis.yml says we should ignore branch
        if ss.get('branch', None) and not config.can_build_branch(ss['branch']):
            defer.returnValue(self.end(SUCCESS))

        # Find the master object
        master = self.build.builder.botmaster.parent

        # Find the scheduler we are going to use to queue actual builds
        all_schedulers = self.build.builder.botmaster.parent.allSchedulers()
        all_schedulers = dict([(sch.name, sch) for sch in all_schedulers])
        sch = all_schedulers[self.scheduler]

        triggered = []

        self.running = True

        for env in config.matrix:
            props_to_set = Properties()
            props_to_set.updateFromProperties(self.build.getProperties())
            props_to_set.update(env["env"], ".travis.yml")
            props_to_set.setProperty("spawned_by",  self.build.build_status.number, "Scheduler")

            triggered.append(sch.trigger(ss_for_trigger, set_props=props_to_set))

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
