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

from .base import BaseFactory
from ..steps import TravisTrigger

class TravisSpawnerFactory(BaseFactory):

    def __init__(self, projectname, scheduler, repository, vcs_type=None, branch=None, username=None, password=None):
        BaseFactory.__init__(self, projectname, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)

        self.addStep(TravisTrigger(
            scheduler=scheduler,
            ))
