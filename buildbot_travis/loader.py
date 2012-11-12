import urlparse, os, shelve

from twisted.python import log

from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.schedulers.basic  import SingleBranchScheduler, AnyBranchScheduler
from buildbot.changes import svnpoller, gitpoller
from buildbot.schedulers.filter import ChangeFilter

from .changes import svnpoller
from .factories import TravisFactory, TravisSpawnerFactory
from .mergereq import mergeRequests
from .config import nextBuild

from yaml import safe_load

def fileIsImportant(change):
    # Ignore "branch created"
    if len(change.files) == 1 and change.files[0] == '':
        return False

    for f in change.files:
        dirname = ''
        if "/" in f:
            dirname, f = f.rsplit("/", 1)

        # Ignore files modified by zest
        if f in ("CHANGES", "CHANGES.rst", "CHANGES.txt", "HISTORY.txt", "HISTORY"):
            continue
        if f == "version.txt":
            continue

        # Ignore badger configuration
        if f == ".badger.yml":
            continue

        return True

    return False


class SVNChangeSplitter(object):

    def __init__(self, repository):
        self.repository = repository
        self.roots = []

    def add(self, repository, branch, project):
        assert repository.startswith(self.repository)
        repository = repository[len(self.repository):]
        self.roots.append((repository, branch, project))
        print self.repository, repository, branch, project

    def split_file(self, path):
        pieces = path.split("/")
        if pieces[0] == 'trunk':
            return 'trunk', '/'.join(pieces[1:])
        elif pieces[0] == 'branches':
            return '/'.join(pieces[0:2]), '/'.join(pieces[2:])
        return None

    def __call__(self, path):
        log.msg("Looking for match for '%s'" % path)
        for root, branch, project in self.roots:
            if path.startswith(root):
                log.msg("Found match - project '%s'" % project)
                f = svnpoller.SVNFile()
                f.project = project
                f.repository = self.repository + root
                path = path[len(root):]
                if not branch:
                    log.msg("Determining branch")
                    where = self.split_file(path)
                    if not where:
                        return None
                    f.branch, f.path = where
                else:
                    log.msg("Trying to force branch")
                    if not path.startswith(branch):
                        log.msg("'%s' doesnt start with '%s'" % (path, branch))
                        continue
                    f.branch = branch
                    f.path = path[len(branch):]
                return f
        log.msg("No match found")
        log.msg(self.roots)


class Loader(object):

    def __init__(self, config, vardir):
        self.config = config
        self.vardir = vardir
        self.passwords = {}
        self.properties = {}
        self.repositories = {}

    def add_password(self, scheme, netloc, username, password):
        self.passwords[(scheme, netloc)] = (username, password)

    def load(self, path):
        for p in safe_load(path).get("projects", []):
            self.define_travis_builder(**p)

    def load_shelve(self, path):
        shelf = shelve.open(path)
        for project in shelf.keys():
            definition = shelf[project]
            l.define_travis_builder(**definition)
        shelf.close()

    def get_spawner_slaves(self):
        from buildbot.buildslave import BuildSlave
        slaves = [s.slavename for s in self.config['slaves'] if isinstance(s, BuildSlave)]
        return slaves

    def get_runner_slaves(self):
        from buildbot.buildslave import AbstractLatentBuildSlave
        slaves = [s.slavename for s in self.config['slaves'] if isinstance(s, AbstractLatentBuildSlave)]
        return slaves

    def define_travis_builder(self, name, repository, branch=None, vcs_type=None, username=None, password=None):
        job_name = "%s-job" % name
        spawner_name = name

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
            name = job_name,
            slavenames = self.get_runner_slaves(),
            properties = self.properties,
            #mergeRequests = mergeRequests,
            mergeRequests = False,
            env = dict(
                DEBIAN_FRONTEND = "noninteractive",
                CI = "true",
                TRAVIS = "true",
                HAS_JOSH_K_SEAL_OF_APPROVAL = "true",
                LANG = "en_GB.UTF-8",
                LC_ALL = "en_GB.UTF-8",
                ),
            factory = TravisFactory(
                repository = repository,
                branch = branch,
                vcs_type = vcs_type,
                username = username,
                password = password,
                ),
             ))

        self.config['schedulers'].append(Triggerable(job_name, [job_name]))


        # Define the builder for a spawer
        self.config['builders'].append(BuilderConfig(
            name = spawner_name,
            nextBuild = nextBuild,
            slavenames = self.get_spawner_slaves(),
            properties = self.properties,
            category = "spawner",
            factory = TravisSpawnerFactory(
                repository = repository,
                branch = branch,
                scheduler = job_name,
                vcs_type = vcs_type,
                username = username,
                password = password,
                ),
            ))

        SchedulerKlass = {True:SingleBranchScheduler, False:AnyBranchScheduler}[bool(branch)]

        self.config['schedulers'].append(SchedulerKlass(
            name = spawner_name,
            builderNames = [spawner_name],
            change_filter = ChangeFilter(project=name),
            onlyImportant = True,
            fileIsImportant = fileIsImportant,
            ))

        setup_poller = dict(git=self.setup_git_poller, svn=self.setup_svn_poller)[vcs_type]
        setup_poller(repository, branch, name, username, password)


    def make_poller_dir(self, name):
        # Set up polling for the projects repository
        # Each poller will get its own directory to store state in
        pollerdir = os.path.join(self.vardir, "pollers", name)
        if not os.path.exists(pollerdir):
            log.msg("Creating pollerdir '%s'" % pollerdir)
            os.makedirs(pollerdir)
        return pollerdir

    def setup_git_poller(self, repository, branch, project, username=None, password=None):
        pollerdir = self.make_poller_dir(project)
        self.config['change_source'].append(gitpoller.GitPoller(
            repourl = repository,
            workdir = pollerdir,
            project = project,
            ))

    def get_repository_root(self, repository, username=None, password=None):
        import subprocess
        options = {}
        cmd = ["svn", "info", repository, "--non-interactive"]
        if username:
            cmd.extend(["--username", username])
        if password:
            cmd.extend(["--password", password])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env={'LC_MESSAGES':'C'})
        s, e = p.communicate()
        for line in s.split("\n"):
            if ":" in line:
                k, v = line.split(": ")
                k = k.strip().lower().replace(" ", "-")
                v = v.strip()
                options[k] = v
        return options["repository-root"] + "/"

    def setup_svn_poller(self, repository, branch, project, username=None, password=None):
        for repo in self.repositories:
            if repository.startswith(repo):
                splitter = self.repositories[repo]
                break
        else:
            repo = self.get_repository_root(repository, username, password)

            scheme, netloc, path, params, query, fragment = urlparse.urlparse(repo)
            name = "%s-%s-%s" % (scheme, netloc.replace(".", "-"), path.rstrip("/").lstrip("/").replace("/", "-"))
            pollerdir = self.make_poller_dir(name)

            splitter = self.repositories[repo] = SVNChangeSplitter(repo)

            self.config['change_source'].append(svnpoller.SVNPoller(
                svnurl = repo,
                cachepath = os.path.join(pollerdir, "pollerstate"),
                project = None,
                split_file = splitter,
                svnuser = username,
                svnpasswd = password,
                ))

        splitter.add(repository, branch, project)

