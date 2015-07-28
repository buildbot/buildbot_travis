import urlparse
import os

from buildbot import config

# TBD use plugins!
from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.buildslave import BuildSlave
from buildbot.buildslave import AbstractLatentBuildSlave
from buildbot.process import factory
from buildbot.plugins import util
from buildbot.plugins import reporters
from buildbot import getVersion
from .important import ImportantManager
from .vcs import addRepository, getSupportedVCSTypes
from .vcs.gerrit import manager as gerritManager
from .steps import TravisSetupSteps
from .steps import TravisTrigger
from yaml import safe_load

import buildbot_travis


class TravisConfigurator(object):

    def __init__(self, config, vardir, latentRunners=False):
        self.config = config
        self.vardir = vardir
        self.latentRunners = latentRunners
        self.passwords = {}
        self.properties = {}
        self.repositories = {}
        self.change_hook_dialects = {}
        config.setdefault("builders", [])
        config.setdefault("schedulers", [])
        config.setdefault("change_source", [])
        config.setdefault("status", [])
        config.setdefault("multiMaster", True)  # we are not really multimaster, but this remove some checks
        config['codebaseGenerator'] = lambda chdict: chdict['project']
        self.config['title'] = os.environ.get('buildbotTitle', "buildbot travis")


    def add_password(self, scheme, netloc, username, password):
        self.passwords[(scheme, netloc)] = (username, password)

    def fromYaml(self, path):
        buildbot_travis.api.setYamlPath(path)
        with open(path) as f:
            y = safe_load(f)

        return self.fromDict(y)

    def fromDict(self, y):
        buildbot_travis.api.setCfg(y)
        self.cfgdict = y
        print y
        self.importantManager = ImportantManager(y.get("not_important_files", []))
        self.defaultEnv = y.get("env", {})
        for k, v in self.defaultEnv.items():
            if not (isinstance(v, list) or isinstance(v, basestring)):
                config.error("'env' values must be strings or lists; key %s is incorrect: %s" % (k, type(v)))
        for p in y.get("projects", []):
            self.define_travis_builder(**p)

        PORT = int(os.environ.get('PORT', 8020))
        self.config['buildbotURL'] = os.environ.get('buildbotURL', "http://localhost:%d/" % (PORT, ))
        # minimalistic config to activate new web UI
        self.config['www'] = dict(port=PORT,
                                  change_hook_dialects=self.change_hook_dialects,
                                  plugins=dict(buildbot_travis={'cfg': self.cfgdict,
                                                                'supported_vcs': getSupportedVCSTypes()}),
                                  versions=[('buildbot_travis', getVersion(__file__))])
        for cs in gerritManager.sources.values():
            self.config.setdefault("services", []).append(
                reporters.GerritStatusPush(server=cs.gerritserver, port=cs.gerritport, username=cs.username)
            )

    def fromDb(self):
        buildbot_travis.api.useDbConfig()
        dbConfig = util.DbConfig(self.config, self.vardir)
        return self.fromDict(dbConfig.get("travis", {}))

    def get_spawner_slaves(self):
        slaves = [s.slavename for s in self.config['slaves'] if isinstance(s, BuildSlave)]
        return slaves

    def get_runner_slaves(self):
        if self.latentRunners:
            BuildSlaveClass = AbstractLatentBuildSlave
        else:
            BuildSlaveClass = BuildSlave
        slaves = [s.slavename for s in self.config['slaves'] if isinstance(s, BuildSlaveClass)]
        return slaves

    def define_travis_builder(self, name, repository, **kwargs):
        name = str(name)
        repository = str(repository)
        job_name = "%s-job" % name
        try_name = "%s-try" % name
        spawner_name = name

        if 'username' not in kwargs and 'password' not in kwargs:
            p = urlparse.urlparse(repository)
            k = (p.scheme, p.netloc)
            if k in self.passwords:
                kwargs['username'], kwargs['password'] = self.passwords[k]

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
            tags=["job", name],
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
        properties = dict(TRAVIS_PULL_REQUEST=False)
        properties.update(self.properties)
        self.config['builders'].append(BuilderConfig(
            name=spawner_name,
            slavenames=self.get_spawner_slaves(),
            properties=properties,
            tags=["trunk", name],
            factory=f
            ))

        if vcsManager.supportsTry:
            properties = dict(TRAVIS_PULL_REQUEST=True)
            properties.update(self.properties)
            # Define the builder for try job
            f = factory.BuildFactory()
            vcsManager.addSourceSteps(f)
            f.addStep(TravisTrigger(
                scheduler=job_name,
            ))

            self.config['builders'].append(BuilderConfig(
                name=try_name,
                slavenames=self.get_spawner_slaves(),
                properties=properties,
                tags=["try", name],
                factory=f
                ))

        vcsManager.setupSchedulers(self.config['schedulers'], spawner_name, try_name,
                                   self.importantManager, codebases)
        vcsManager.setupChangeSource(self.config['change_source'])
        res = vcsManager.setupChangeSource(self.config['change_source'])
        if res is not None:
            self.change_hook_dialects.update(res)
