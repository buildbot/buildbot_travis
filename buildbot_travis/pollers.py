import os

from twisted.python import log

from buildbot.changes import svnpoller, gitpoller
from .changes import svnpoller


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


class PollersMixin(object):

    def setup_poller(self, repository, vcs_type=None, branch=None, project=None,
                     username=None, password=None):
        if not vcs_type:
            if repository.startswith("https://svn."):
                vcs_type = "svn"
            elif repository.startswith("git://github.com/"):
                vcs_type = "git"

        setup_poller = dict(git=self.setup_git_poller, svn=self.setup_svn_poller)[vcs_type]
        setup_poller(repository, branch, project, username, password)

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
            repourl=repository,
            workdir=pollerdir,
            project=project
            ))

    def get_repository_root(self, repository, username=None, password=None):
        import subprocess
        options = {}
        cmd = ["svn", "info", repository, "--non-interactive"]
        if username:
            cmd.extend(["--username", username])
        if password:
            cmd.extend(["--password", password])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env={'LC_MESSAGES': 'C'})
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
                svnurl=repo,
                cachepath=os.path.join(pollerdir, "pollerstate"),
                project=None,
                split_file=splitter,
                svnuser=username,
                svnpasswd=password,
                ))

        splitter.add(repository, branch, project)
