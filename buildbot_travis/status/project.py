
import time
import operator
import re
import urllib

from twisted.internet import defer
from twisted.python import log

from buildbot import util
from buildbot.status import builder
from buildbot.status.web.base import HtmlResource
from buildbot.changes import changes
from buildbot.status.web.base import path_to_build
from buildbot.status.results import SUCCESS

from buildbot_travis.factories import TravisSpawnerFactory
from buildbot_travis.travisyml import TravisYml, TravisYmlInvalid

from .build import Build
from .delete_project import DeleteProject


class ProjectStatus(HtmlResource):

    def __init__(self, project):
        HtmlResource.__init__(self)
        self.project = project

    def getHeadBuild(self, builder):
        """ Get the most recent build for the given builder. """
        build = builder.getBuild(-1)
        if build is None:
            build = builder.getBuild(-2)
        return build

    def getBuild(self, req, build):
        result = dict(
            revisions=build.getChanges(),
            properties=build.getProperties().asDict(),
            number=build.number,
        )

        if not build.isFinished():
            result['color'] = 'building'
        elif build.results == SUCCESS:
            result['color'] = "success"
        else:
            result['color'] = "failure"

        return result

    def getBuilds(self, request):
        status = self.getStatus(request)
        spawner = status.getBuilder(self.project)

        depth = 0
        b = self.getHeadBuild(spawner)
        while b and depth < 25:
            yield self.getBuild(request, b)
            b = b.getPreviousBuild()
            depth += 1

    @defer.inlineCallbacks
    def getPendingBuilds(self, req):
        spawner = self.getStatus(req).getBuilder(self.project)
        pending = yield spawner.getPendingBuildRequestStatuses()

        builds = []
        for b in pending:
            source = yield b.getSourceStamp()
            if source.changes:
                last = source.changes[-1]
                info = dict(
                    revision=last.revision,
                    comments=last.comments,
                )
            else:
                info = dict(
                    revision="HEAD",
                    comments="Pending manual build",
                )
            builds.append(info)
        defer.returnValue(builds)

    @defer.inlineCallbacks
    def content(self, request, cxt):
        request.setHeader('Cache-Control', 'no-cache')

        cxt['project'] = self.project

        cxt['pending'] = yield self.getPendingBuilds(request)
        cxt['builds'] = list(self.getBuilds(request))

        cxt['shutting_down'] = self.getStatus(request).shuttingDown

        templates = request.site.buildbot_service.templates
        template = templates.get_template("project.html")
        data = template.render(cxt)
        defer.returnValue(data)

    def getChild(self, path, request):
        if path == "delete":
            return DeleteProject(self.project)
        builder = self.getStatus(request).getBuilder(self.project)
        build = builder.getBuild(int(path))
        if build:
            return Build(build)
        return HtmlResource.getChild(self, path, request)


class Projects(HtmlResource):

    def getBuilders(self, req):
        status = self.getStatus(req)
        for name in status.botmaster.builderNames:
            b = status.botmaster.builders[name]
            if not isinstance(b.config.factory, TravisSpawnerFactory):
                continue

            p = {}
            p['name'] = b.name

            if b.builder_status.currentBuilds:
                p['status'] = 'building'
            else:
                build = b.builder_status.getLastFinishedBuild()
                if not build:
                    p['status'] = "nobuilds"
                elif build.results == SUCCESS:
                    p['status'] = "success"
                else:
                    p['status'] = "failure"

            yield p

    def getBuilderNames(self, req):
        return [b['name'] for b in self.getBuilders(req)]

    @defer.inlineCallbacks
    def content(self, req, cxt):
        req.setHeader('Cache-Control', 'no-cache')

        # This is where the meat will go, and it will use inlineCallbacks...
        yield defer.succeed(None)

        cxt['projects'] = sorted(list(self.getBuilders(req)))
        cxt['shutting_down'] = self.getStatus(req).shuttingDown

        templates = req.site.buildbot_service.templates
        template = templates.get_template("projects.html")
        data = template.render(cxt)
        defer.returnValue(data)

    def getChild(self, path, req):
        if path in self.getBuilderNames(req):
            return ProjectStatus(path)
        return HtmlResource.getChild(self, path, req)


class About(HtmlResource):

    def content(self, req, cxt):
        templates = req.site.buildbot_service.templates
        template = templates.get_template("about.html")
        return template.render(cxt)
