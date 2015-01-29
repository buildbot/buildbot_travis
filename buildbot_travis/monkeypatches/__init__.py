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

import inspect


def patch_process_build_Build_getSourceStamp():
    from buildbot.process.build import Build
    args, varargs, keywords, defaults = inspect.getargspec(Build.getSourceStamp)
    if not "codebase" in args:
        old_getSourceStamp = Build.getSourceStamp
        def getSourceStamp(self, codebase=''):
            return old_getSourceStamp(self)
        Build.getSourceStamp = getSourceStamp

def patch_all():
    patch_process_build_Build_getSourceStamp()
