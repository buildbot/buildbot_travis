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

def mergeRequests(builder, req1, req2):
    if not req1.source.canBeMergedWith(req2.source):
       return False

    props1 = set((k,v1) for (k, v1, v2) in req1.properties.asList() if v2 == ".travis.yml")
    props2 = set((k,v1) for (k, v1, v2) in req2.properties.asList() if v2 == ".travis.yml")

    if len(props1 - props2) > 0 or len(props2 - props1) > 0:
        return False

    return True
