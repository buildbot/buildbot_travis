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

from twisted.web import static
from twisted.web.util import Redirect
from twisted.application import strports
from twisted.internet.protocol import Factory
from twisted.internet import defer
from twisted.python import log
from twisted.internet import reactor

from buildbot.status.web import baseweb

from . import websocketstatus

from .add_project import AddProjectForm, AddProject
from .project import Projects, ProjectStatus, About

import os, re


class CiWebStatus(baseweb.WebStatus):

    allowed_projects_prefix = []

    def __init__(self, *args, **kwargs):
        self.dashboard = None

        if 'dashboard' in kwargs:
            self.dashboard = kwargs['dashboard']
            del kwargs['dashboard']

        if 'vardir' in kwargs:
            self.vardir = kwargs['vardir']
            del kwargs['vardir']

        baseweb.WebStatus.__init__(self, *args, **kwargs)

    def setupWebsocket(self, status):
        from txws import WebSocketFactory
        f = Factory()
        f.protocol = websocketstatus.WSBuildHandler
        f.status = status
        service = strports.service(self.dashboard, WebSocketFactory(f))
        service.setServiceParent(self)

    def setupSite(self):
        if self.dashboard:
            status = self.site.status = self.getStatus()
            self.setupWebsocket(status)
            self.putChild("10footci", websocketstatus.WSBuildResource())

        path = os.path.join(os.path.dirname(__file__), "public_html")
        self.putChild("buildbot_travis_assets", baseweb.StaticFile(path))

        self.putChild("", Redirect("/projects"))
        self.putChild("projects", Projects())
        self.putChild("about", About())

        self.putChild("add_form", AddProjectForm())
        self.putChild("add", AddProject(self, os.path.join(self.vardir, "travis")))

        baseweb.WebStatus.setupSite(self)
