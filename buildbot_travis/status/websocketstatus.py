import json, urlparse

from twisted.application import strports
from twisted.internet.protocol import Protocol, Factory
from twisted.web import resource
from twisted.web.static import File
from twisted.internet import task

from buildbot import interfaces, util
from buildbot.status import base
from buildbot.status.web.base import HtmlResource

try:
    from buildbot.status.results import FAILURE, SUCCESS, EXCEPTION, Results
except ImportError:
    from buildbot.status.builder import FAILURE,SUCCESS, EXCEPTION, Results

from twisted.python import log

from twisted.internet.protocol import Protocol

class WSBuildHandler(Protocol, base.StatusReceiver):

    def dataReceived(self, msg):
        log.msg('msg: ', self.transport.getPeer())

    def connectionMade(self):
        self.status = self.factory.status

        self.status.subscribe(self)

        builders = self.status.getBuilderNames()
        builds = []
        for buildername in builders:
            builder = self.status.getBuilder(buildername)
            build = builder.getBuild(-1)
            if not build:
                continue

            b = self.getBuildMetadata(build)
            if b:
                builds.append(b)

        def compare_fn(x, y):
            # This sort function should make sure old builds are at the top of the list, so
            # they get pushed over the websocket first
            xtimestamp = x.get("finished", x.get("started", 0))
            ytimestamp = y.get("finished", y.get("started", 0))
            if xtimestamp > ytimestamp:
                return 1
            if xtimestamp < ytimestamp:
                return -1
            return 0

        builds.sort(compare_fn)

        for b in builds:
            self.transport.write(json.dumps(b))

    def connectionLost(self, reason):
        if self.status:
            self.status.unsubscribe(self)
            self.status = None

    def getBuildMetadata(self, build):
        builder = build.getBuilder()
        builder_conf = filter(lambda n: n.name == builder.getName(), builder.master.config.builders)[0]

        if builder_conf.properties.get('classification', None) != "ci":
            return

        try:
            from buildbot_travis.factories import TravisFactory
            if isinstance(builder_conf.factory, TravisFactory):
                return
        except ImportError:
            pass

        if not build.finished:
            status = "building"
        else:
            status = Results[build.getResults()]

        attrs = {
          'id': "%s-%s" % (builder.getName(), build.getNumber()),
          'builder': builder.getName(),
          'status': status,
          #'buildURL': self.status.getURLForThing(build),
          #'buildbotURL': self.status.getBuildbotURL(),
          'buildText': build.getText(),
          'buildProperties': dict(((x, y or '') for (x,y,z) in build.getProperties().asList())),
          'slavename': build.getSlavename(),
          'reason':  build.getReason(),
          'responsibleUsers': build.getResponsibleUsers(),
          'branch': "",
          'revision': "",
          'patch': "",
          'changes': [],
          }

        if build.finished:
            attrs['finished'] = build.finished
        if build.started:
            attrs['started'] = build.started

        #ss = build.getSourceStamp()
        #if ss:
        #    attrs['branch'] = ss.branch
        #    attrs['revision'] = ss.revision
        #    attrs['patch'] = ss.patch
        #    attrs['changes'] = [x.asDict() for x in ss.changes[:]]

        return attrs

    def builderAdded(self, builderName, builder):
        return self

    def buildStarted(self, name, build):
        b = self.getBuildMetadata(build)
        if b:
            self.push(b)
        return self

    def buildFinished(self, name, build, results):
        b = self.getBuildMetadata(build)
        if b:
            self.push(b)

    def push(self, build):
        data = json.dumps(build)
        self.transport.write(data)


class WSBuildResource(HtmlResource):
    tite = "All Builds (10-foot view)"

    def content(self, req, cxt):
        cxt['bb_url'] = self.getStatus(req).getBuildbotURL()
        bb_url = urlparse.urlsplit(cxt['bb_url'])

        scheme = "wss" if bb_url[0] == "https" else "ws"
        netloc = bb_url.hostname + ":8087"
        path = "/ws/build"

        cxt['ws_url'] = urlparse.urlunparse((scheme, netloc, path, '', '',''))

        template = req.site.buildbot_service.templates.get_template("10foot.html")
        return template.render(**cxt)

