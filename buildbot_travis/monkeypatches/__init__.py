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
