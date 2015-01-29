# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2012-2103 Isotoma Limited

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
