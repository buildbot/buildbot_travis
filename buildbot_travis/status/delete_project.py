
from twisted.python import log
from twisted.internet import reactor
from buildbot.status.web.base import ActionResource
import os, shelve


class DeleteProject(ActionResource):

    def __init__(self, project):
        self.project = project

    def performAction(self, req):
        CAME_FROM = "/projects"

        path = os.path.join(req.site.buildbot_service.vardir, "travis")

        shelf = shelve.open(path, writeback=False)
        if not self.project in shelf:
            return ((CAME_FROM, "No such project"))

        log.msg("Deleting project '%s' by user request" % self.project)

        del shelf[self.project]
        shelf.sync()
        shelf.close()

        reactor.callLater(0, req.site.buildbot_service.master.reconfig)

        return (("/projects", ""))

