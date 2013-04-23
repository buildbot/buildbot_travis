
import urllib, time
from twisted.python import log
from twisted.internet import defer

from buildbot.status.web.base import HtmlResource, \
     css_classes, path_to_build, path_to_builder
from buildbot.status.results import SUCCESS, WARNINGS, FAILURE, SKIPPED
from buildbot.status.results import EXCEPTION, RETRY
from buildbot import util


css_classes = {
    SUCCESS: "success",
    WARNINGS: "warning",
    FAILURE: "important",
    SKIPPED: "",
    EXCEPTION: "important",
    RETRY: "important",
    None: "",
    }


class Build(HtmlResource):
    addSlash = True

    def __init__(self, build_status):
        HtmlResource.__init__(self)
        self.build_status = build_status

    def getPageTitle(self, request):
        return "%s build #%d" % (
            self.build_status.getBuilder().getName(),
            self.build_status.getNumber(),
            )

    @defer.inlineCallbacks
    def getPending(self, request):
        nr = self.build_status.getNumber()

        status = self.getStatus(request)
        job = status.getBuilder(self.build_status.getBuilder().getName() + "-job")

        builds = []
        pending = yield job.getPendingBuildRequestStatuses()

        for b in pending:
            source = yield b.getSourceStamp()
            submitTime = yield b.getSubmitTime()
            bsid = yield b.getBsid()
            properties = yield \
                b.master.db.buildsets.getBuildsetProperties(bsid)

            if properties["spawned_by"][0] != nr:
                continue

            info = {}

            info['number'] = "?"

            env = info['environment'] = {}
            for name, value in properties.items():
                value, source = value
                if source != ".travis.yml":
                    continue
                env[name] = value

            # How long has it been pending?
            info['start'] = time.strftime("%b %d %H:%M:%S",
                                      time.localtime(submitTime))
            info['elapsed'] = util.formatInterval(util.now() - submitTime)

            info['result_css'] = "pending"

            builds.append(info)

        defer.returnValue(builds)


    def getChildren(self, request):
        nr = self.build_status.getNumber()

        status = self.getStatus(request)
        job = status.getBuilder(self.build_status.getBuilder().getName() + "-job")

        b = job.getBuild(-1)
        if not b:
            b = job.getBuild(-2)

        while b:
            spawned_by = b.getProperty("spawned_by", None)
            if spawned_by == nr:
                yield b
            if spawned_by and spawned_by < nr:
                break
            b = b.getPreviousBuild()
    
    def getChildBuild(self, req, b):
        cxt = self.getCommonBuildInfo(req, b)

        env = cxt['environment'] = {}
        for name, value, source in b.getProperties().asList():
            if source != ".travis.yml":
                continue
            env[name] = value

        cxt['steps'] = []

        for s in b.getSteps():
            step = {'name': s.getName() }

            if s.isFinished():
                if s.isHidden():
                    continue

                step['css_class'] = css_classes[s.getResults()[0]]
                (start, end) = s.getTimes()
                step['time_to_run'] = util.formatInterval(end - start)
            elif s.isStarted():
                if s.isWaitingForLocks():
                    step['css_class'] = "waiting"
                    step['time_to_run'] = "waiting for locks"
                else:
                    step['css_class'] = "running"
                    step['time_to_run'] = "running"
            else:
                step['css_class'] = "not_started"
                step['time_to_run'] = ""

            cxt['steps'].append(step)

            link = step['link'] = path_to_build(req, b) + "/steps/%s" % urllib.quote(s.getName(), safe='')
            step['text'] = " ".join(s.getText())
            step['urls'] = map(lambda x:dict(url=x[1],logname=x[0]), s.getURLs().items())

            step['logs']= []
            for l in s.getLogs():
                logname = l.getName()
                step['logs'].append(dict(
                    link = link + "/logs/%s" % urllib.quote(logname, safe=''),
                    name = logname,
                    ))

        return cxt

    def getCommonBuildInfo(self, req, b):
        cxt = {}
        cxt['number'] = b.getNumber()

        if not b.isFinished():
            step = b.getCurrentStep()
            if not step:
                cxt['current_step'] = "[waiting for Lock]"
            else:
                if step.isWaitingForLocks():
                    cxt['current_step'] = "%s [waiting for Lock]" % step.getName()
                else:
                    cxt['current_step'] = step.getName()
            when = b.getETA()
            if when is not None:
                cxt['when'] = util.formatInterval(when)
                cxt['when_time'] = time.strftime("%H:%M:%S",
                                                time.localtime(time.time() + when))

            cxt['result_css'] = "building"
        else:
            cxt['result_css'] = css_classes[b.getResults()]

        (start, end) = b.getTimes()
        cxt['start'] = time.ctime(start)
        if end:
            cxt['end'] = time.ctime(end)
            cxt['elapsed'] = util.formatInterval(end - start)
        else:
            now = util.now()
            cxt['elapsed'] = util.formatInterval(now - start)

        return cxt

    @defer.inlineCallbacks
    def content(self, req, cxt):
        b = self.build_status
        status = self.getStatus(req)
        req.setHeader('Cache-Control', 'no-cache')

        cxt['b'] = b
        cxt['path_to_builder'] = path_to_builder(req, b.getBuilder())

        ssList = b.getSourceStamps()
        sourcestamps = cxt['sourcestamps'] = ssList

        all_got_revisions = b.getAllGotRevisions()
        cxt['got_revisions'] = all_got_revisions

        cxt.update(self.getCommonBuildInfo(req, b))

        cxt['builds'] = []
        for c in self.getChildren(req):
            cxt['builds'].append(self.getChildBuild(req, c))

        pending = yield self.getPending(req)
        for p in pending:
            cxt['builds'].append(p)

        ps = cxt['properties'] = []
        for name, value, source in b.getProperties().asList():
            if not isinstance(value, dict):
                cxt_value = unicode(value)
            else:
                cxt_value = value
            p = { 'name': name, 'value': cxt_value, 'source': source}
            if len(cxt_value) > 500:
                p['short_value'] = cxt_value[:500]
            ps.append(p)
        
        cxt['responsible_users'] = list(b.getResponsibleUsers())

        exactly = True
        has_changes = False
        for ss in sourcestamps:
            exactly = exactly and (ss.revision is not None)
            has_changes = has_changes or ss.changes
        cxt['exactly'] = (exactly) or b.getChanges()
        cxt['has_changes'] = has_changes
        cxt['build_url'] = path_to_build(req, b)
        cxt['authz'] = self.getAuthz(req)

        cxt['shutting_down'] = status.shuttingDown

        template = req.site.buildbot_service.templates.get_template("travis.build.html")
        defer.returnValue(template.render(**cxt))

