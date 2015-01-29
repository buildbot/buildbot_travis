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

from .mergereq import mergeRequests
from .loader import Loader

# We sometimes monkey patch older buildbots to work like newer buildbots
# That's because at present buildbot doesn't try to maintain any API compat at
# all...
from .monkeypatches import patch_all
patch_all()
del patch_all
