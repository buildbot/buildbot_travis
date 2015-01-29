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

class Sadface:
    brdict = None

def nextBuild(builder, requests):
    """
    This nextBuild function stops builds from having a spawner fire up
    if there are no free builders
    """

    if not builder.builder_status:
        log.msg("nextBuild: Builder %s does not have a builder_status" % builder)
        return Sadface()

    job = builder.master.getStatus().getBuilder("%s-job" % builder.name)
    for slavename in job.slavenames:
        slave = builder.master.botmaster.slaves[slavename]
        if not slave.canStartBuild():
            continue
        if hasattr(slave, "substantiation_deferred") and slave.substantiation_deferred:
            continue

        # it looks like the job builder might have some slots available
        return requests[0]

    log.msg("nextBuild: Tried to start spawner '%s' but not jobs slots available" % builder.name)
    return Sadface()
