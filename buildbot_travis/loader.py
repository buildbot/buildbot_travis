import urlparse
from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable

from .factories import TravisFactory, TravisSpawnerFactory
from .mergereq import mergeRequests

from yaml import safe_load

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

    def define_travis_builder(self, name, repository, vcs_type=None, username=None, password=None):
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
            slavenames = integration_slaves.any(),
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
            slavenames = integration_slaves.any(),
            category = "spawner",
            factory = TravisSpawnerFactory(
                repository = repository,
                scheduler = name,
                vcs_type = vcs_type,
                username = username,
                password = password,
                ),
            ))

        c['schedulers'].apppend(Scheduler(
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
            c['change_source'].append(gitpoller.GitPoller(
                repourl=repository,
                workdir=pollerdir,
                project=name,
                ))

        elif vcs_type == "svn":
            c['change_source'].append(svnpoller.SVNPoller(
                svnurl=repository,
                cachepath=os.path.join(pollerdir, "pollerstate"),
                project=name,
                split_file=svnpoller.split_file_branches,
                svnuser=config.SVN_USERNAME,
                svnpasswd=config.SVN_PASSWORD,
                ))

