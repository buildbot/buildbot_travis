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
