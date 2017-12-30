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

from __future__ import absolute_import, division, print_function

from twisted.internet import defer

from buildbot.process.properties import Properties
from buildbot.steps.trigger import Trigger

from .base import ConfigurableStepMixin


class TravisTrigger(Trigger, ConfigurableStepMixin):
    def __init__(self, scheduler, **kwargs):
        if "name" not in kwargs:
            kwargs['name'] = 'trigger'
        self.config = None
        Trigger.__init__(
            self,
            waitForFinish=True,
            schedulerNames=[scheduler],
            haltOnFailure=True,
            flunkOnFailure=True,
            sourceStamps=[],
            alwaysUseLatest=False,
            updateSourceStamp=False,
            **kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.config = yield self.getStepConfig()

        rv = yield Trigger.run(self)
        defer.returnValue(rv)

    def createTriggerProperties(self, props):
        return props

    def getSchedulersAndProperties(self):
        sch = self.schedulerNames[0]
        reason_excluded_env = self.config.global_env.keys()

        triggered_schedulers = []
        for env in self.config.matrix:
            props_to_set = Properties()
            props_to_set.setProperty("TRAVIS_PULL_REQUEST",
                                     self.getProperty("TRAVIS_PULL_REQUEST"),
                                     "inherit")
            flat_env = {}
            for k, v in env.items():
                if k == "env":
                    props_to_set.update(v, ".travis.yml")
                    flat_env.update(v)
                else:
                    props_to_set.setProperty(k, v, ".travis.yml")
                    flat_env[k] = v
            tags = self.build.builder.config.tags
            for tag in ["trunk", "try"]:
                if tag in tags:
                    tags.remove(tag)
            label_tags = sorted(
                str(self.config.label_mapping.get(k, k)) + ':' +
                str(self.config.label_mapping.get(v, v))
                for k, v in flat_env.items() if k not in reason_excluded_env)
            props_to_set.setProperty("virtual_builder_name", u" ".join(tags + label_tags),
                                     "spawner")
            props_to_set.setProperty("virtual_builder_tags", tags + label_tags,
                                     "spawner")
            props_to_set.setProperty("matrix_label", u"/".join(label_tags),
                                     "spawner")

            triggered_schedulers.append((sch, props_to_set))
        return triggered_schedulers
