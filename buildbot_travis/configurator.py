import urlparse
import os
import shelve

from buildbot import config
from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.buildslave import BuildSlave
from buildbot.buildslave import AbstractLatentBuildSlave

from buildbot.process import factory
from .important import ImportantManager
from .vcs import addRepository, getSupportedVCSTypes
from .steps import TravisSetupSteps
from .steps import TravisTrigger
from yaml import safe_load

import buildbot_travis


class TravisConfigurator(object):

    def __init__(self, config, vardir):
        self.config = config
        self.vardir = vardir
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
        buildbot_travis.api.setYamlPath(path)
        with open(path) as f:
            y = safe_load(f)
        self.yamlcfg = y
        self.importantManager = ImportantManager(y.get("not_important_files", []))
        self.defaultEnv = y.get("env", {})
        for k, v in self.defaultEnv.items():
            if not (isinstance(v, list) or isinstance(v, str)):
                config.error("'env' values must be strings or lists; key %s is incorrect: %s" % (k, type(v)))
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

    def define_travis_builder(self, name, repository, **kwargs):
        job_name = "%s-job" % name
        try_name = "%s-try" % name
        spawner_name = name

        if 'username' not in kwargs and 'password' not in kwargs:
            p = urlparse.urlparse(repository)
            k = (p.scheme, p.netloc)
            if k in self.passwords:
                kwargs['username'], kwargs['password'] = self.passwords[k]

        branch = kwargs.get("branch")
        codebases = {spawner_name: {'repository': repository}}
        for subrepo in kwargs.get('subrepos', []):
            codebases[subrepo['project']] = {'repository': subrepo['repository']}

        vcsManager = addRepository(name, dict(name=name, repository=repository, **kwargs))
        vcsManager.vardir = self.vardir

        # Define the builder for the main job
        f = factory.BuildFactory()
        vcsManager.addSourceSteps(f)
        f.addStep(TravisSetupSteps())

        self.config['builders'].append(BuilderConfig(
            name=job_name,
            slavenames=self.get_runner_slaves(),
            properties=self.properties,
            collapseRequests=False,
            env=self.defaultEnv,
            factory=f
            ))

        self.config['schedulers'].append(Triggerable(
            name=job_name,
            builderNames=[job_name],
            codebases=codebases,
            ))

        # Define the builder for a spawner
        f = factory.BuildFactory()
        vcsManager.addSourceSteps(f)
        f.addStep(TravisTrigger(
            scheduler=job_name,
        ))

        self.config['builders'].append(BuilderConfig(
            name=spawner_name,
            slavenames=self.get_spawner_slaves(),
            properties=self.properties,
            category="spawner",
            factory=f
            ))

        if vcsManager.supportsTry:
            # Define the builder for try job
            f = factory.BuildFactory()
            vcsManager.addSourceSteps(f)
            f.addStep(TravisTrigger(
                scheduler=job_name,
            ))

            self.config['builders'].append(BuilderConfig(
                name=try_name,
                slavenames=self.get_spawner_slaves(),
                properties=self.properties,
                category="try",
                factory=f
                ))

        self.config['title'] = os.environ.get('buildbotTitle', "buildbot travis")
        PORT = int(os.environ.get('PORT', 8020))
        self.config['buildbotURL'] = os.environ.get('buildbotURL', "http://localhost:%d/" % (PORT, ))

        # minimalistic config to activate new web UI
        self.config['www'] = dict(port=PORT, allowed_origins=["*"],
                                  plugins=dict(buildbot_travis={'cfg': self.yamlcfg,
                                                                'supported_vcs': getSupportedVCSTypes()}))

        vcsManager.setupSchedulers(self.config['schedulers'], spawner_name, try_name,
                                   self.importantManager, codebases)
        vcsManager.setupChangeSource(self.config['change_source'])
