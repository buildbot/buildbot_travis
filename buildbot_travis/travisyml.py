import re
from yaml import safe_load

TRAVIS_HOOKS = ("before_install", "install", "after_install", "before_script", "script", "after_script")


class TravisYmlInvalid(Exception):
    pass


class TravisYml(object):
    """
    Loads a .travis.yml file and parses it.
    """

    def __init__(self):
        self.language = None
        self.environments = [{}]
        self.environments_keys = []
        for hook in TRAVIS_HOOKS:
            setattr(self, hook, [])
        self.branch_whitelist = None
        self.branch_blacklist = None
        self.email = TravisYmlEmail()
        self.irc = TravisYmlIrc()

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
        self.parse_hooks()
        self.parse_branches()
        self.parse_notifications_email()
        self.parse_notifications_irc()

    def parse_language(self):
        try:
            self.language = self.config['language']
        except:
            raise TravisYmlInvalid("'language' parameter is missing")

    def parse_env(self, env):
        props = {}
        if not env.strip():
            return props

        prev = None
        vars = env.split(" ")
        for v in vars:
            k, v = v.split("=")
            props[k] = v

            ek = self.environments_keys
            if not k in ek:
                if prev:
                    ek.insert(ek.index(prev)+1, k)
                else:
                    ek.insert(0, k)
            prev = k

        return props

    def parse_envs(self):
        env = self.config.get("env", None)
        if env is None:
            return
        elif isinstance(env, basestring):
            self.environments_keys = []
            self.environments = [self.parse_env(env)]
        elif isinstance(env, list):
            self.environments_keys = []
            self.environments = [self.parse_env(e) for e in env]
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

        raise TravisYmlInvalid("'branches' parameter contains neither 'only' nor 'except'")

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
        if not self.branch_whitelist is None:
            if self._match_branch(branch, self.branch_whitelist):
                return True
            return False
        if not self.branch_blacklist is None:
            if self._match_branch(branch, self.branch_blacklist):
                return False
            return True
        return True


class _NotificationsMixin(object):

    def parse_failure_success(self, settings):
        self.success = settings.get("on_success", self.success)
        if not self.success in ("always", "never", "change"):
            raise TravisYmlInvalid("Invalid value '%s' for on_success" % self.success)

        self.failure = settings.get("on_failure", self.failure)
        if not self.failure in ("always", "never", "change"):
            raise TravisYmlInvalid("Invalid value '%s' for on_failure" % self.failure)
   

class TravisYmlEmail(_NotificationsMixin):

    def __init__(self):
        self.enabled = True
        self.addresses = []
        self.success = "change"
        self.failure = "always"

    def parse(self, settings):
        if settings == False:
            self.enabled = False
            return

        if isinstance(settings, list):
            self.addresses = settings
            return

        if not isinstance(settings, dict):
            raise TravisYmlInvalid("Exepected a False, a list of addresses or a dictionary at noficiations.email")

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

