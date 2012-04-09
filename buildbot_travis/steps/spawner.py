from buildbot.process import buildstep
from buildbot.process.buildstep import LoggingBuildStep, SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from twisted.spread import pb
from twisted.internet import defer
import StringIO

from buildbot_travis.travisyml import TravisYml

# This is duplicated for older buildbots...
def makeStatusRemoteCommand(step, remote_command, args):
    if hasattr(buildstep.RemoteCommand, "useLogDelayed"):
        self = buildstep.RemoteCommand(remote_command, args)
        callback = lambda arg: step.step_status.addLog('stdio')
        self.useLogDelayed('stdio', callback, True)
    else:
        class StatusRemoteCommand(buildstep.RemoteCommand):
            def __init__(self, remote_command, args):
                buildstep.RemoteCommand.__init__(self, remote_command, args)
                self.rc = None
                self.stderr = ''
            
            def remoteUpdate(self, update):
                #log.msg('StatusRemoteCommand: update=%r' % update)
                if 'rc' in update:
                    self.rc = update['rc']
                if 'stderr' in update:
                    self.stderr = self.stderr + update['stderr'] + '\n'
        self = StatusRemoteCommand(remote_command, args)
    
    return self

class _FileWriter(pb.Referenceable):
    def __init__(self):
        self.fp = StringIO.StringIO()
        self.data = ""
    
    def remote_write(self, data):
        self.fp.write(data)
    
    def remote_utime(self, accessed_modified):
        pass
    
    def remote_close(self):
        self.data = self.fp.getvalue()
        self.fp.close()
        self.fp = None
    
    def cancel(self):
        self.fp = None
        self.data = ""


class TravisTrigger(LoggingBuildStep):
    
    def __init__(self, scheduler, **kwargs):
        if not "name" in kwargs:
            kwargs['name'] = 'trigger'
        #if not "description" in kwargs:
        #    kwargs['description'] = kwargs['name']
        LoggingBuildStep.__init__(self, **kwargs)
        self.addFactoryArguments(scheduler=scheduler)
        
        self.scheduler = scheduler
    
    def start(self):
        version = self.slaveVersion("uploadFile")
        if not version:
            m = "slave is too old, does not know about uploadFile"
            raise BuildSlaveTooOldError(m)
        
        self.fw = _FileWriter()
        
        # default arguments
        args = {
            'slavesrc': ".travis.yml",
            'workdir': "build",
            'writer': self.fw,
            'maxsize': None,
            'blocksize': 16384,
            'keepstamp': False,
        }
        
        self.cmd = makeStatusRemoteCommand(self, 'uploadFile', args)
        d = self.runCommand(self.cmd)
        
        @d.addErrback
        def cancel(res):
            self.fw.cancel()
            return res
        
        d.addCallback(self._really_start).addErrback(self.failed)
    
    def _really_start(self, res):
        config = TravisYml()
        config.parse(self.fw.data)
        
        ss = self.build.getSourceStamp()
        got = self.build.getProperty('got_revision')
        if got:
            ss = ss.getAbsoluteSourceStamp(got)

        # Stop the build early if .travis.yml says we should ignore branch
        if ss.branch and not config.can_build_branch(ss.branch):
            return self.finished(SUCCESS)           
        
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
        
        return self.finished(SUCCESS)
