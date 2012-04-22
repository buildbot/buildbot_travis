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
        for hook in TRAVIS_HOOKS:
            setattr(self, hook, [])
        self.branch_whitelist = None
        self.branch_blacklist = None

    def parse(self, config_input):
        self.parse_dict(safe_load(config_input))

    def parse_dict(self, config):
        self.config = config
        self.parse_language()
        self.parse_envs()
        self.parse_hooks()
        self.parse_branches()

    def parse_language(self):
        try:
            self.language = self.config['language']
        except:
            raise TravisYmlInvalid("'language' parameter is missing")

    def parse_env(self, env):
        props = {}
        if not env.strip():
            return props
        
        vars = env.split(" ")
        for v in vars:
            k, v = v.split("=")
            props[k] = v
        
        return props

    def parse_envs(self):
        env = self.config.get("env", None)
        if env is None:
            return
        elif isinstance(env, basestring):
            self.environments = [self.parse_env(env)]
        elif isinstance(env, list):
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

