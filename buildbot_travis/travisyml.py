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

import re
from yaml import safe_load

TRAVIS_HOOKS = ("before_install", "install", "after_install",
                "before_script", "script", "after_script")


class TravisYmlInvalid(Exception):
    pass


def parse_env_string(env, global_env=None):
    props = {}
    if global_env:
        props.update(global_env)
    if not env.strip():
        return props

    _vars = env.split(" ")
    for v in _vars:
        k, v = v.split("=", 1)
        props[k] = v

    return props


class TravisYml(object):

    """
    Loads a .travis.yml file and parses it.
    """

    def __init__(self):
        self.language = None
        self.image = None
        self.environments = [{}]
        self.matrix = []
        for hook in TRAVIS_HOOKS:
            setattr(self, hook, [])
        self.branch_whitelist = None
        self.branch_blacklist = None
        self.email = TravisYmlEmail()
        self.irc = TravisYmlIrc()
        self.config = None

    def parse(self, config_input):
        try:
            d = safe_load(config_input)
        except Exception as e:
            raise TravisYmlInvalid("Invalid YAML data\n" + str(e))
        self.parse_dict(d)

    def parse_dict(self, config):
        self.config = config
        self.parse_language()
        self.parse_envs()
        self.parse_matrix()
        self.parse_hooks()
        self.parse_branches()
        self.parse_notifications_email()
        self.parse_notifications_irc()

    def parse_language(self):
        try:
            self.language = self.config['language']
        except:
            raise TravisYmlInvalid("'language' parameter is missing")

    def parse_envs(self):
        env = self.config.get("env", None)
        if env is None:
            return
        elif isinstance(env, basestring):
            self.environments = [parse_env_string(env)]
        elif isinstance(env, list):
            self.environments = [parse_env_string(e) for e in env]
        elif isinstance(env, dict):
            global_env = {}
            for e in env.get('global', []):
                global_env.update(parse_env_string(e))
            self.environments = [
                parse_env_string(e, global_env) for e in env.get('matrix', [''])]
        else:
            raise TravisYmlInvalid("'env' parameter is invalid")

    def parse_hooks(self):
        for hook in TRAVIS_HOOKS:
            commands = self.config.get(hook, [])
            if isinstance(commands, basestring):
                commands = [commands]
            if not isinstance(commands, list):
                raise TravisYmlInvalid("'%s' parameter is invalid" % hook)
            setattr(self, hook, commands)

    def parse_branches(self):
        branches = self.config.get("branches", None)
        if not branches:
            return

        if "only" in branches:
            if not isinstance(branches['only'], list):
                raise TravisYmlInvalid('branches.only should be a list')
            self.branch_whitelist = branches['only']
            return

        if "except" in branches:
            if not isinstance(branches['except'], list):
                raise TravisYmlInvalid('branches.except should be a list')
            self.branch_blacklist = branches['except']
            return

        raise TravisYmlInvalid(
            "'branches' parameter contains neither 'only' nor 'except'")

    def parse_matrix(self):
        matrix = []

        # First of all, build the implicit matrix
        for lang in self.config.get("python", ["python2.6"]):
            for env in self.environments:
                matrix.append(dict(
                    python=lang,
                    env=env,
                ))

        cfg = self.config.get("matrix", {})

        for env in cfg.get("exclude", []):
            matchee = env.copy()
            matchee['env'] = parse_env_string(matchee.get('env', ''))
            if matchee in matrix:
                matrix.remove(matchee)

        for env in cfg.get("include", []):
            e = env.copy()
            e['env'] = parse_env_string(e.get('env', ''))
            matrix.append(e)

        self.matrix = matrix

    def parse_notifications_irc(self):
        notifications = self.config.get("notifications", {})
        self.irc.parse(notifications.get("irc", {}))

    def parse_notifications_email(self):
        notifications = self.config.get("notifications", {})
        self.email.parse(notifications.get("email", {}))

    def _match_branch(self, branch, lst):
        for b in lst:
            if b.startswith("/") and b.endswith("/"):
                if re.search(b[1:-1], branch):
                    return True
            else:
                if b == branch:
                    return True
        return False

    def can_build_branch(self, branch):
        if self.branch_whitelist is not None:
            if self._match_branch(branch, self.branch_whitelist):
                return True
            return False
        if self.branch_blacklist is not None:
            if self._match_branch(branch, self.branch_blacklist):
                return False
            return True
        return True


class _NotificationsMixin(object):
    success = 'never'
    failure = 'never'

    def parse_failure_success(self, settings):
        self.success = settings.get("on_success", self.success)
        if self.success not in ("always", "never", "change"):
            raise TravisYmlInvalid(
                "Invalid value '%s' for on_success" % self.success)

        self.failure = settings.get("on_failure", self.failure)
        if self.failure not in ("always", "never", "change"):
            raise TravisYmlInvalid(
                "Invalid value '%s' for on_failure" % self.failure)


class TravisYmlEmail(_NotificationsMixin):

    def __init__(self):
        self.enabled = True
        self.addresses = []
        self.success = "change"
        self.failure = "always"

    def parse(self, settings):
        if not settings:
            self.enabled = False
            return

        if isinstance(settings, list):
            self.addresses = settings
            return

        if not isinstance(settings, dict):
            raise TravisYmlInvalid(
                "Exepected a False, a list of addresses or a dictionary at noficiations.email")

        self.addresses = settings.get("recipients", self.addresses)

        self.parse_failure_success(settings)


class TravisYmlIrc(_NotificationsMixin):

    def __init__(self):
        self.enabled = False
        self.channels = []
        self.template = []
        self.success = "change"
        self.failure = "always"
        self.notice = False
        self.join = True

    def parse(self, settings):
        if not settings:
            return

        self.enabled = True
        self.channels = settings.get("channels", [])
        self.template = settings.get("template", [])
        self.notice = settings.get("use_notice", False)
        self.join = not settings.get("skip_join", False)

        self.parse_failure_success(settings)
