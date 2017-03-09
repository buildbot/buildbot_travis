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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

def mergeRequests(builder, req1, req2):
    if not req1.source.canBeMergedWith(req2.source):
        return False

    props1 = set((k, v1)
                 for (k, v1, v2) in req1.properties.asList() if v2 == ".travis.yml")
    props2 = set((k, v1)
                 for (k, v1, v2) in req2.properties.asList() if v2 == ".travis.yml")

    if len(props1 - props2) > 0 or len(props2 - props1) > 0:
        return False

    return True
