import urlparse
import os
import shelve

from twisted.python import log

from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.schedulers.basic import SingleBranchScheduler
from buildbot.schedulers.basic import AnyBranchScheduler
from buildbot.schedulers.filter import ChangeFilter
from buildbot.buildslave import BuildSlave
from buildbot.buildslave import AbstractLatentBuildSlave

from .factories import TravisFactory, TravisSpawnerFactory
from .mergereq import mergeRequests
from .important import ImportantManager
from .pollers import PollersMixin

from yaml import safe_load


class TravisConfigurator(PollersMixin):

    def __init__(self, config, vardir):
        self.config = config
        self.vardir = vardir
        print config, vardir
        self.passwords = {}
        self.properties = {}
        self.repositories = {}
        config.setdefault("builders", [])
        config.setdefault("schedulers", [])
        config.setdefault("change_source", [])

        config['codebaseGenerator'] = lambda chdict: chdict['project']

    def add_password(self, scheme, netloc, username, password):
        self.passwords[(scheme, netloc)] = (username, password)

    def fromYaml(self, path):
        with open(path) as f:
            y = safe_load(f)
        self.importantManager = ImportantManager(y.get("not_important_files", []))
        self.defaultEnv = y.get("env", {})
        for p in y.get("projects", []):
            self.define_travis_builder(**p)

    def fromShelve(self, path):
        shelf = shelve.open(path)
        for project in shelf.keys():
            definition = shelf[project]
            self.define_travis_builder(**definition)
        shelf.close()

    def get_spawner_slaves(self):
        slaves = [s.slavename for s in self.config['slaves'] if isinstance(s, BuildSlave)]
        return slaves

    def get_runner_slaves(self):
        slaves = [s.slavename for s in self.config['slaves'] if isinstance(s, AbstractLatentBuildSlave)]
        return slaves

    def define_travis_builder(self, name, repository, branch=None, vcs_type=None, username=None,
                              password=None, subrepos=None):
        job_name = "%s-job" % name
        spawner_name = name

        if not username and not password:
            p = urlparse.urlparse(repository)
            k = (p.scheme, p.netloc)
            if k in self.passwords:
                username, password = self.passwords[k]

        codebases = {spawner_name: {'repository': repository}}
        if subrepos:
            for subrepo in subrepos:
                codebases[subrepo['project']] = {'repository': subrepo['repository']}

        # Define the builder for the main job
        self.config['builders'].append(BuilderConfig(
            name=job_name,
            slavenames=self.get_runner_slaves(),
            properties=self.properties,
            collapseRequests=False,
            env=self.defaultEnv,
            factory=TravisFactory(
                projectname=spawner_name,
                repository=repository,
                branch=branch,
                vcs_type=vcs_type,
                username=username,
                password=password,
                subrepos=subrepos,
                )
            ))

        self.config['schedulers'].append(Triggerable(
            name=job_name,
            builderNames=[job_name],
            codebases=codebases,
            ))

        # Define the builder for a spawer
        self.config['builders'].append(BuilderConfig(
            name=spawner_name,
            slavenames=self.get_spawner_slaves(),
            properties=self.properties,
            category="spawner",
            factory=TravisSpawnerFactory(
                projectname=spawner_name,
                repository=repository,
                branch=branch,
                scheduler=job_name,
                vcs_type=vcs_type,
                username=username,
                password=password,
                ),
            ))

        SchedulerKlass = {True: SingleBranchScheduler, False: AnyBranchScheduler}[bool(branch)]

        self.config['schedulers'].append(SchedulerKlass(
            name=spawner_name,
            builderNames=[spawner_name],
            change_filter=ChangeFilter(project=name),
            onlyImportant=True,
            fileIsImportant=self.importantManager.fileIsImportant,
            codebases=codebases,
            ))

        self.setup_poller(repository, vcs_type, branch, name, username, password)
