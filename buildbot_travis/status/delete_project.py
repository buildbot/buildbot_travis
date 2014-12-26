# Copyright 2012-2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
