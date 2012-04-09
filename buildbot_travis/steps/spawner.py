
from buildbot.process import buildstep
from buildbot.process.buildstep import LoggingBuildStep, SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from twisted.spread import pb
from twisted.internet import defer
import StringIO

from .base import ConfigurableStep

class TravisTrigger(ConfigurableStep):
    
    def __init__(self, scheduler, **kwargs):
        if not "name" in kwargs:
            kwargs['name'] = 'trigger'
        #if not "description" in kwargs:
        #    kwargs['description'] = kwargs['name']
        LoggingBuildStep.__init__(self, **kwargs)
        self.addFactoryArguments(scheduler=scheduler)
        
        self.scheduler = scheduler

    @defer.inlineCallbacks 
    def start(self):
        config = yield self.getStepConfig()
        
        ss = self.build.getSourceStamp()
        got = self.build.getProperty('got_revision')
        if got:
            ss = ss.getAbsoluteSourceStamp(got)

        # Stop the build early if .travis.yml says we should ignore branch
        if ss.branch and not config.can_build_branch(ss.branch):
            defer.returnValue(self.finished(SUCCESS))
        
        # Find the scheduler we are going to use to queue actual builds
        all_schedulers = self.build.builder.botmaster.parent.allSchedulers()
        all_schedulers = dict([(sch.name, sch) for sch in all_schedulers])
        sch = all_schedulers[self.scheduler]
        
        for env in config.environments:
            props_to_set = Properties()
            props_to_set.updateFromProperties(self.build.getProperties())
            props_to_set.update(env, ".travis.yml")
            
            if hasattr(ss, "getSourceStampSetId"):
                master = self.build.builder.botmaster.parent # seriously?!
                d = ss.getSourceStampSetId(master)
            else:
                d = defer.succeed(ss)
            
            def _trigger_build(ss_setid):
                sch.trigger(ss_setid, set_props=props_to_set)
            d.addCallback(_trigger_build)
        
        defer.returnValue(self.finished(SUCCESS))

