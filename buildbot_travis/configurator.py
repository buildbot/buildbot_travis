import urlparse
import os

from buildbot.config import error as config_error

# TBD use plugins!
from buildbot.config import BuilderConfig
from buildbot.schedulers.forcesched import StringParameter, CodebaseParameter
from buildbot.schedulers.triggerable import Triggerable
from buildbot.worker import Worker
from buildbot.worker import AbstractLatentWorker
from buildbot.process import factory
from buildbot.plugins import util
from buildbot import getVersion
from .important import ImportantManager
from .vcs import addRepository, getSupportedVCSTypes
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
        self.cfgdict = {}
        self.importantManager = None
        self.change_hook_dialects = {}
        config.setdefault("builders", [])
        config.setdefault("schedulers", [])
        config.setdefault("change_source", [])
        config.setdefault("services", [])
        config.setdefault("status", [])
        self.defaultEnv = {}
        self.defaultStages = []
        # we are not really multimaster, but this remove some checks
        config.setdefault("multiMaster", True)
        config['codebaseGenerator'] = lambda chdict: chdict['project']
        self.config['title'] = os.environ.get(
            'buildbotTitle', "buildbot travis")

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
        self.importantManager = ImportantManager(
            y.get("not_important_files", []))
        self.defaultEnv = y.get("env", {})
        for k, v in self.defaultEnv.items():
            if not (isinstance(v, list) or isinstance(v, basestring)):
                config_error(
                    "'env' values must be strings or lists ; key %s is incorrect: %s" % (k, type(v)))
        for p in y.get("projects", []):
            self.define_travis_builder(**p)
        self.defaultStages = y.get("stages", [])
        for s in self.defaultStages:
            if not isinstance(s, basestring):
                config_error(
                    "'stages' values must be strings ; stage %s is incorrect: %s" % (s, type(s)))

        PORT = int(os.environ.get('PORT', 8020))
        self.config['buildbotURL'] = os.environ.get(
            'buildbotURL', "http://localhost:%d/" % (PORT, ))
        # minimalistic config to activate new web UI
        self.config['www'] = dict(port=PORT,
                                  change_hook_dialects=self.change_hook_dialects,
                                  plugins=dict(buildbot_travis={'cfg': self.cfgdict,
                                                                'supported_vcs': getSupportedVCSTypes()}),
                                  versions=[('buildbot_travis', getVersion(__file__))])

    def fromDb(self):
        buildbot_travis.api.useDbConfig()
        dbConfig = util.DbConfig(self.config, self.vardir)
        return self.fromDict(dbConfig.get("travis", {}))

    def get_spawner_workers(self):
        workers = [s.workername for s in self.config[
            'workers'] if isinstance(s, Worker)]
        return workers

    def get_runner_workers(self):
        if self.latentRunners:
            WorkerClass = AbstractLatentWorker
        else:
            WorkerClass = Worker
        workers = [s.workername for s in self.config[
            'workers'] if isinstance(s, WorkerClass)]
        return workers

    def define_travis_builder(self, name, repository, tags=None, **kwargs):
        name = str(name)
        repository = str(repository)
        job_name = "%s-job" % name
        try_name = "%s-try" % name
        deploy_name = "%s-deploy" % name
        spawner_name = name
        if tags is None:
            tags = []

        def formatTag(tag):
            if isinstance(tag, basestring):
                return str(tag)
            return str(tag['text'])

        tags = map(formatTag, tags)
        if 'username' not in kwargs and 'password' not in kwargs:
            p = urlparse.urlparse(repository)
            k = (p.scheme, p.netloc)
            if k in self.passwords:
                kwargs['username'], kwargs['password'] = self.passwords[k]

        codebases = {spawner_name: {'repository': repository}}
        for subrepo in kwargs.get('subrepos', []):
            codebases[subrepo['project']] = {
                'repository': subrepo['repository']}

        vcsManager = addRepository(
            name, dict(name=name, repository=repository, **kwargs))
        vcsManager.vardir = self.vardir

        # Define the builder for the main job
        f = factory.BuildFactory()
        vcsManager.addSourceSteps(f)
        f.addStep(TravisSetupSteps())

        self.config['builders'].append(BuilderConfig(
            name=job_name,
            workernames=self.get_runner_workers(),
            properties=self.properties,
            collapseRequests=False,
            env=self.defaultEnv,
            tags=["job", name] + tags,
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
            workernames=self.get_spawner_workers(),
            properties=properties,
            tags=["trunk", name] + tags,
            factory=f
        ))

        # Define the builder for the deployment of the project
        f = factory.BuildFactory()
        vcsManager.addSourceSteps(f)
        f.addStep(TravisSetupSteps())

        # To manage deployment properly (with change traceability),
        # we need the version and the target deployment environment or "stage"
        version = StringParameter(name='version', label='GIT tag',
                                  hide=False, required=False, size=20)
        stage = StringParameter(name='stage', label='Stage',
                                hide=False, required=False,size=20)

        dep_properties = [version, stage]

        self.config['builders'].append(BuilderConfig(
            name=deploy_name,
            workernames=self.get_runner_workers(),
            env=self.defaultEnv,
            tags=["deploy", name] + tags,
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
                workernames=self.get_spawner_workers(),
                properties=properties,
                tags=["try", name] + tags,
                factory=f
            ))

        vcsManager.setupSchedulers(self.config['schedulers'], spawner_name, try_name, deploy_name,
                                   self.importantManager, codebases, dep_properties)
        vcsManager.setupReporters(
            self.config['services'], spawner_name, try_name, codebases)
        res = vcsManager.setupChangeSource(self.config['services'])
        if res is not None:
            self.change_hook_dialects.update(res)
