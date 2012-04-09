import os, re

from buildbot.steps.transfer import FileDownload
from buildbot.steps.shell import ShellCommand
from buildbot.process.buildstep import LogLineObserver

from isotoma.buildbot.factories import CiFactory

def sibpath(path):
    return os.path.join(os.path.dirname(__file__), path)


class TravisLogLineObserver(LogLineObserver):

    _final_matcher = re.compile("==> Executed (?P<commands>\d+) commands")

    nbCommands = 0

    def outLineReceived(self, line):
        if line.startswith("==> "):
            self.nbCommands += 1
            self.step.setProgress("commands", self.nbCommands)

        # Last output looks like this:
        # ==> Executed %d commands
        r = self._final_matcher.search(line)
        if r:
            self.nbCommands = int(r.groups("commands")[0])
            self.step.setProgress("commands", self.nbCommands)


class TravisRunner(ShellCommand):

    haltOnFailure = True
    flunkOnFailure = True

    progressMetrics = ShellCommand.progressMetrics + ('commands',)

    def __init__(self, step, **kwargs):
        kwargs['name'] = step
        kwargs['description'] = step
        kwargs['command'] = "./travis-runner %s" % step

        ShellCommand.__init__(self, **kwargs)

        self.addFactoryArguments(
            step = step,
            )

    def setupEnvironment(self, cmd):
        """ Turn all build properties into environment variables """
        ShellCommand.setupEnvironment(self, cmd)

        env = {}
        for k, v in self.build.getProperties().properties.items():
            env[str(k)] = str(v[0])

        cmd.args['env'].update(env)

    def setupLogfiles(self, cmd, logfiles):
        self.observer = TravisLogLineObserver()
        self.addLogObserver('stdio', self.observer)
        ShellCommand.setupLogfiles(self, cmd, logfiles)

    def describe(self, done=False):
        description = ShellCommand.describe(self, done)
        if done:
            description.append('%d commands' % self.step_status.getStatistic('commands', 0))
        return description

    def createSummary(self, log):
        self.step_status.setStatistic('commands', self.observer.nbCommands)

    def hideStepIf(self, results, _):
	"""
        Check to see how many commands were run - if we didnt running any
        then hide this step
        """
        return int(self.step_status.getStatistic('commands', 0)) == 0


class TravisFactory(CiFactory):

    def __init__(self, repository, vcs_type=None, branch=None, username=None, password=None):
        CiFactory.__init__(self, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)

        self.addStep(FileDownload(
            mastersrc=sibpath("travis-runner.py"),
            slavedest="travis-runner",
            mode=0755,
            ))

        self.addStep(ShellCommand(
            name="apt-get-update",
            description="apt-get-update",
            flunkOnFailure=True,
            haltOnFailure=True,
            command="sudo apt-get update",
            ))

        self.addStep(ShellCommand(
            name="apt-get-deps",
            description="apt-get-deps",
            flunkOnFailure=True,
            haltOnFailure=True,
            command="sudo apt-get install -y -q python-yaml",
            ))

        for step in ("before-install", "install", "after-install", "before-script", "script", "after-script"):
            self.addStep(TravisRunner(
                step = step,
                ))


from buildbot.process import buildstep
from buildbot.process.buildstep import LoggingBuildStep, SUCCESS, FAILURE, EXCEPTION
from buildbot.process.properties import Properties
from twisted.spread import pb
from twisted.internet import defer
import StringIO
import yaml

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

    def _match_branch(self, branch, list):
        for b in lst:
            if b.startswith("/") and b.endswith("/"):
                if re.search(b[1:-1], branch):
                    return True
            else:
                if b == branch:
                    return True
        return False

    def _check_branches(self, branch, branches):
        if not branch:
            return True
        if not isinstance(branches, dict):
            return True

        if "only" in branches:
            if self._match_branch(branch, branches["only"]):
                return True
            return False
        elif "except" in branches:
            if self._match_branch(branch, branches["except"]):
                return False
            return True

        return True

    def _env_to_dict(self, env):
        props = {}
        if not env.strip():
            return props

        vars = env.split(" ")
        for v in vars:
            k, v = v.split("=")
            props[k] = v

        return props

    def _really_start(self, res):
        config = yaml.load(self.fw.data)

        ss = self.build.getSourceStamp()
        got = self.build.getProperty('got_revision')
        if got:
            ss = ss.getAbsoluteSourceStamp(got)

        branches = config.get("branches", None)
        if not self._check_branches(ss.branch, branches):
            return self.finished(SUCCESS)           

        # Find the scheduler we are going to use to queue actual builds
        all_schedulers = self.build.builder.botmaster.parent.allSchedulers()
        all_schedulers = dict([(sch.name, sch) for sch in all_schedulers])
        sch = all_schedulers[self.scheduler]

        # The environment field might be a string not a list!
        # It might even be an empty list.. Make sure it is valid
        environments = config.get("env", [])
        if not isinstance(environments, list):
            environments = [environments]
        if not len(environments):
            environments.append('')

        for env in environments:
            props_to_set = Properties()
            props_to_set.updateFromProperties(self.build.getProperties())
            props_to_set.update(self._env_to_dict(env), ".travis.yml")
           
            if hasattr(ss, "getSourceStampSetId"):
                master = self.build.builder.botmaster.parent # seriously?!
                d = ss.getSourceStampSetId(master)
            else:
                d = defer.succeed(ss)

            def _trigger_build(ss_setid):
                sch.trigger(ss_setid, set_props=props_to_set)
            d.addCallback(_trigger_build)

        return self.finished(SUCCESS)


class TravisSpawnerFactory(CiFactory):

    def __init__(self, scheduler, repository, vcs_type=None, branch=None, username=None, password=None):
        CiFactory.__init__(self, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)

        self.addStep(TravisTrigger(
            scheduler=scheduler,
            ))

