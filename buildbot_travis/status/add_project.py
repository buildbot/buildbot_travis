
from twisted.web import static
from twisted.web.util import Redirect
from twisted.application import strports
from twisted.internet.protocol import Factory
from twisted.internet import defer
from twisted.python import log
from twisted.internet import reactor

from buildbot.status.web import baseweb
from buildbot.status.web.base import HtmlResource, ActionResource

from isotoma.buildbot.status import websocketstatus

from buildbot_travis.status import Projects, About

import os, shelve, re

class AddProjectForm(HtmlResource):

    def content(self, req, cxt):
        template = req.site.buildbot_service.templates.get_template("travis.add.html")
        #return (template.render(**cxt))
        return template.render(cxt)


class AddProject(ActionResource):

    def __init__(self, status, path):
        self.status = status
        self.path = path

    def performAction(self, req):
        CAME_FROM = "/add_form"

        name = req.args.get("name", [""])[0].strip().lower()
        if not name:
            return ((CAME_FROM, "You must specify the name of the project"))

        if not re.match('^[a-z0-9\-\.]+$', name):
            return ((CAME_FROM, "Name can currently only contain a-z, 0-9, '-' and '.', and lower case will be forced for consistency"))

        repository = req.args.get("repository", [""])[0].strip()
        if not repository:
            return ((CAME_FROM, "You must specify an SVN repository or GitHub repo"))

        for prefix in self.status.allowed_projects_prefix:
            if repository.startswith(prefix):
                break
        else:
            return ((CAME_FROM, "Only repos at these locations are supported at present: %s" % ",".join(self.status.allowed_projects_prefix))) 

        branch = req.args.get("branch", [""])[0].strip()
        #if not branch:
        #    return ((CAME_FROM, "You must specify an SVN repository or GitHub repo"))

        shelf = shelve.open(self.path, writeback=False)

        if name in shelf:
            return ((CAME_FROM, "Project is already defined"))

        for p in shelf.keys():
            details = shelf[p]
            if details["repository"] == repository:
                if not branch:
                    return ((CAME_FROM, "Repository is already defined for project '%s'" % details["name"]))
                if branch == details.get("branch", ""):
                    return ((CAME_FROM, "Repository/branch pair already defined for project '%s'" % details["name"]))

        payload = dict(
            name = name,
            repository = repository,
            )
        if branch:
            payload['branch'] = branch

        shelf[name] = payload

        shelf.sync()
        shelf.close()

        reactor.callLater(0, req.site.buildbot_service.master.reconfig)

        return (("/projects", ""))


