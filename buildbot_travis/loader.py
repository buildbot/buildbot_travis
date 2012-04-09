import urlparse, os
from buildbot.config import BuilderConfig as BuilderConfig_
from buildbot.schedulers.triggerable import Triggerable
from buildbot.schedulers.basic  import Scheduler
from buildbot.changes import svnpoller, gitpoller
from buildbot.schedulers.filter import ChangeFilter

from .factories import TravisFactory, TravisSpawnerFactory
from .mergereq import mergeRequests

from yaml import safe_load

# I have to support oldere Buildbot. Woe is me.
class BuilderConfig(BuilderConfig_):
    def __init__(self, mergeRequests=None, **kwargs):
        BuilderConfig_.__init__(self, **kwargs)
        self.mergeRequests = mergeRequests
    def getConfigDict(self):
        rv = BuilderConfig_.getConfigDict(self)
        if self.mergeRequests:
            rv['mergeRequests'] = self.mergeRequests
        return rv


class Loader(object):

    def __init__(self, config, vardir):
        self.config = config
        self.vardir = vardir
        self.passwords = {}
        self.properties = {}

    def add_password(self, scheme, netloc, username, password):
        self.passwords[(scheme, netloc)] = (username, password)

    def load(self, path):
        for p in safe_load(path).get("projects", []):
            self.define_travis_builder(**p)

    def get_slaves(self):
        return self.config['slaves']

    def define_travis_builder(self, name, repository, vcs_type=None, username=None, password=None):
        if not repository.endswith("/"):
            repository = repository + "/"

        if not vcs_type:
            if repository.startswith("https://svn."):
                vcs_type = "svn"
            elif repository.startswith("git://github.com/"):
                vcs_type = "git"

        if not username and not password:
            p = urlparse.urlparse(repository)
            k = (p.scheme, p.netloc)
            if k in self.passwords:
                username, password = self.passwords[k]

        # Define the builder for the main job
        self.config['builders'].append(BuilderConfig(
            name = name,
            slavenames = self.get_slaves(),
            properties = self.properties,
            mergeRequests = mergeRequests,
            factory = TravisFactory(
                repository = repository,
                vcs_type = vcs_type,
                username = username,
                password = password,
                ),
             ))

        self.config['schedulers'].append(Triggerable(name, [name]))


        # Define the builder for a spawer
        self.config['builders'].append(BuilderConfig(
            name = "%s-spawner" % name,
            slavenames = self.get_slaves(),
            category = "spawner",
            factory = TravisSpawnerFactory(
                repository = repository,
                scheduler = name,
                vcs_type = vcs_type,
                username = username,
                password = password,
                ),
            ))

        self.config['schedulers'].append(Scheduler(
            name = "%s-spawner" % name,
            builderNames = ["%s-spawner" % name],
            change_filter = ChangeFilter(project=name)
            ))

        # Set up polling for the projects repository
        # Each poller will get its own directory to store state in
        pollerdir = os.path.join(self.vardir, "pollers", name)
        if not os.path.exists(pollerdir):
            os.makedirs(pollerdir)

        if vcs_type == "git":
            self.config['change_source'].append(gitpoller.GitPoller(
                repourl = repository,
                workdir = pollerdir,
                project = name,
                ))

        elif vcs_type == "svn":
            self.config['change_source'].append(svnpoller.SVNPoller(
                svnurl = repository,
                cachepath = os.path.join(pollerdir, "pollerstate"),
                project = name,
                split_file = svnpoller.split_file_branches,
                svnuser = username,
                svnpasswd = password,
                ))

