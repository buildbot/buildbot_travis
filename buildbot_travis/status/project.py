
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
from buildbot.status.web.console import getResultsClass
from buildbot.status.web.base import path_to_build
from buildbot.status.results import SUCCESS

from buildbot_travis.factories import TravisSpawnerFactory 
from buildbot_travis.envgraph import EnvMap
from buildbot_travis.travisyml import TravisYml, TravisYmlInvalid


class ProjectStatus(HtmlResource):

    def __init__(self, project):
        HtmlResource.__init__(self)
        self.project = project

    def getHeadBuild(self, builder):
        """Get the most recent build for the given builder.
        """
        build = builder.getBuild(-1)

        # HACK: Work around #601, the head build may be None if it is
        # locked.
        if build is None:
            build = builder.getBuild(-2)

        return build

    def iterBuilds(self, builder):
        b = self.getHeadBuild(builder)
        while b:
            yield b
            b = b.getPreviousBuild() 

    def getEnvironment(self, build):
        env = {}
        for k, v, s in build.getProperties().asList():
            if s != ".travis.yml":
                continue
            env[k] = v
        return env

    def getEnvironmentTuple(self, build):
        env = self.getEnvironment(build)
        return tuple((str(k), str(env[k])) for k in sorted(env.keys()))

    def getStatuses(self, req, builds, envmap):
        bdata = {}
        for b in builds:
            k = self.getEnvironmentTuple(b)
            if k in bdata:
                continue
            bdata[k] = d = {}
      
            d["color"] = getResultsClass(b.getResults(), None, not b.isFinished())
            d['url'] = path_to_build(req, b)
            d['properties'] = b.getProperties().asDict()
            d['number'] = b.number

            for step in b.getSteps():
                (result, reason) = step.getResults()
                if result != builder.SUCCESS:
                    failure = d['failure'] = {}
                    name = failure['step'] = step.getName()
                    failure['reason'] = reason
                    logs = failure['logs'] = []
                    failure['firstline'] = ''
                    failure['env'] = self.getEnvironmentTuple(b)
                    if step.getLogs():
                        for log in step.getLogs():
                            logname = log.getName()
                            if logname in (".travis.yml, "):
                                continue
                            logurl = req.childLink(
                              "../builders/%s/builds/%s/steps/%s/logs/%s" % 
                                (urllib.quote(b.builder.name),
                                 b.getNumber(),
                                 urllib.quote(name),
                                 urllib.quote(logname)))
                            firstline = log.getTextWithHeaders().split("\n")[0]
                            logs.append(dict(url=logurl, name=logname, firstline=firstline))

                        failure['firstline'] = logs[-1]['firstline']

                    break

        ordered = bdata.keys()
        ordered.sort()

        for key in ordered:
            yield bdata[key]

    def getBuild(self, req, build, builds, envmap):
        result = dict(
            revisions = build.getChanges(),
            builds = list(self.getStatuses(req, builds, envmap)),
            color = getResultsClass(build.getResults(), None, not build.isFinished),
            url = "hello",
            properties = build.getProperties().asDict(),
            number = build.number,
            )

        counters = result['counters'] = {}
        counters['success'] = counters['failure'] = 0
        for b in result['builds']:
            color = b['color']
            counters[color] = counters.get(color, 0) + 1

        return result

    def getBuilds(self, request, envmap):
        status = self.getStatus(request)

        spawner = status.getBuilder(self.project)
        job = status.getBuilder(self.project + "-job")

        revisions = {}
        for b in self.iterBuilds(job):
            spawnedby = b.getProperty("spawned_by", None)
            if spawnedby is None:
                continue
            r = revisions.setdefault(spawnedby, [])
            r.append(b)

        depth = 0
        b = self.getHeadBuild(spawner)
        while b and depth < 25:
            number = b.getProperty("buildnumber", 0)
            yield self.getBuild(request, b, revisions.get(number, []), envmap)
            b = b.getPreviousBuild()
            depth += 1

    def getConfiguration(self, request):
        status = self.getStatus(request)
        spawner = status.getBuilder(self.project)
        b = self.getHeadBuild(spawner)
        while b:
            for step in b.getSteps():
                if not step.getLogs():
                    continue
                for log in step.getLogs():
                    if log.getName() == ".travis.yml":
                        try:
                            config = TravisYml()
                            config.parse(log.getText())
                            return config
                        except TravisYmlInvalid:
                            pass
            b = b.getPreviousBuild()
        raise ValueError("Could not find a valid .travis.yml in build history")

    def content(self, request, cxt):
        request.setHeader('Cache-Control', 'no-cache')

        cxt['project'] = self.project

        config = self.getConfiguration(request)

        example = EnvMap(config.environments_keys)
        for env in config.environments:
            example.add(env)

        cxt['builds'] = list(self.getBuilds(request, example))

        cxt['environments'] = list(example.iter_all_depths())

        templates = request.site.buildbot_service.templates
        template = templates.get_template("project.html")
        data = template.render(cxt)
        return data


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

