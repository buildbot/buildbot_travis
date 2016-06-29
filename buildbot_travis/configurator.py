import urlparse
import os
import uuid
import traceback

from buildbot.config import error as config_error

# TBD use plugins!
from buildbot.config import BuilderConfig
from buildbot.schedulers.forcesched import StringParameter
from buildbot.schedulers.triggerable import Triggerable
from buildbot.worker import Worker
from buildbot.process import factory
from buildbot.plugins import util
from buildbot.plugins import worker
from buildbot import getVersion
from buildbot.www.authz.endpointmatchers import EndpointMatcherBase, Match
from twisted.internet import defer
from .important import ImportantManager
from .vcs import addRepository, getSupportedVCSTypes
from .steps import TravisSetupSteps
from .steps import TravisTrigger
from yaml import safe_load
from buildbot.interfaces import ILatentWorker

import buildbot_travis


class TravisEndpointMatcher(EndpointMatcherBase):

    def __init__(self, **kwargs):
        EndpointMatcherBase.__init__(self, **kwargs)

    def match(self, ep, action="get", options=None):
        print ep
        if "/".join(ep).startswith("buildbot_travis/api/config"):
            return defer.succeed(Match(self.master))
        return defer.succeed(None)


class TravisConfigurator(object):

    def __init__(self, config, vardir, latentRunners=False):
        self.config = config
        self.vardir = vardir
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
        self.createWorkerConfig()
        self.importantManager = ImportantManager(
            y.setdefault("not_important_files", []))
        self.defaultEnv = y.setdefault("env", {})
        for k, v in self.defaultEnv.items():
            if not (isinstance(v, list) or isinstance(v, basestring)):
                config_error(
                    "'env' values must be strings or lists ; key %s is incorrect: %s" % (k, type(v)))
        for p in y.setdefault("projects", []):
            self.define_travis_builder(**p)
        self.defaultStages = y.setdefault("stages", [])
        for s in self.defaultStages:
            if not isinstance(s, basestring):
                config_error(
                    "'stages' values must be strings ; stage %s is incorrect: %s" % (s, type(s)))

        PORT = int(os.environ.get('PORT', 8010))
        self.config['buildbotURL'] = os.environ.get(
            'buildbotURL', "http://localhost:%d/" % (PORT, ))

        db_url = os.environ.get('BUILDBOT_DB_URL')
        if db_url is not None:
            self.config.setdefault('db', {'db_url': db_url})

        # minimalistic config to activate new web UI
        self.config['www'] = dict(port=PORT,
                                  change_hook_dialects=self.change_hook_dialects,
                                  plugins=dict(buildbot_travis={
                                      'supported_vcs': getSupportedVCSTypes()}),
                                  versions=[('buildbot_travis', getVersion(__file__))])
        self.config.setdefault('protocols', {'pb': {'port': 9989}})
        self.createAuthConfig()

    def configAssertContains(self, cfg, names):
        hasError = False
        for n in names:
            if n not in cfg:
                config_error("auth requires parameter {} but only has {}".format(n, cfg))
                hasError = True
        return not hasError

    def execCustomCode(self, code, required_variables):
        l = {}
        # execute the code with empty global, and a given local context (that we return)
        try:
            exec code in {}, l
        except Exception:
            config_error("custom code generated an exception {}:".format(traceback.format_exc()))
            raise
        for n in required_variables:
            if n not in l:
                config_error("custom code does not generate variable {}: {} {}".format(n, code, l))

        return l

    def createAuthConfig(self):
        if 'auth' not in self.cfgdict:
            return
        authcfg = self.cfgdict['auth']
        if 'type' not in authcfg:
            return

        createAuthConfigMethod = 'createAuthConfig' + authcfg['type']

        if not hasattr(self, createAuthConfigMethod):
            config_error("auth type {} is not supported".format(authcfg['type']))
            return

        auth = getattr(self, createAuthConfigMethod)(authcfg)
        if auth is None:
            return
        self.config['www']['auth'] = auth
        if 'authztype' not in authcfg:
            return

        createAuthzConfigMethod = 'createAuthzConfig' + authcfg['authztype']
        if not hasattr(self, createAuthzConfigMethod):
            config_error("authz type {} is not supported".format(authcfg['authztype']))
            return

        authz = getattr(self, createAuthzConfigMethod)(authcfg)
        if authz:
            self.config['www']['authz'] = authz

    def createAuthConfigNone(self, authcfg):
        return None

    def createAuthConfigGitHub(self, authcfg):
        if not self.configAssertContains(authcfg, ['clientid', 'clientsecret']):
            return None
        return util.GitHubAuth(authcfg["clientid"], authcfg["clientsecret"])

    def createAuthConfigGoogle(self, authcfg):
        if not self.configAssertContains(authcfg, ['clientid', 'clientsecret']):
            return None
        return util.GoogleAuth(authcfg["clientid"], authcfg["clientsecret"])

    def createAuthConfigGitLab(self, authcfg):
        if not self.configAssertContains(authcfg, ['clientid', 'clientsecret', 'instanceUri']):
            return None

        return util.GitLabAuth(authcfg["instanceUri"], authcfg["clientid"], authcfg["clientsecret"])

    def createAuthConfigCustom(self, authcfg):
        if not self.configAssertContains(authcfg, ['customcode']):
            return None

        return self.execCustomCode(authcfg["customcode"], ['auth'])['auth']

    def getDefaultAllowRules(self, admins):
        epms = [
            util.AnyEndpointMatcher(role=admin, defaultDeny=False)
            for admin in admins]
        epms += [
            TravisEndpointMatcher(role=admin)
            for admin in admins]
        return epms + [
            util.StopBuildEndpointMatcher(role="owner"),
            util.RebuildBuildEndpointMatcher(role="owner"),
        ]

    def createAuthzConfigGroups(self, authcfg):
        if not self.configAssertContains(authcfg, ['groups']):
            return None

        return util.Authz(self.getDefaultAllowRules(admins=authcfg['groups']),
                          [util.RolesFromGroups(groupPrefix="")])

    def createAuthzConfigEmails(self, authcfg):
        if not self.configAssertContains(authcfg, ['emails']):
            return None

        return util.Authz(self.getDefaultAllowRules(admins=['admins']),
                          [util.RolesFromEmails(role="admins", emails=authcfg['emails'])])

    def createAuthzConfigCustom(self, authcfg):
        if not self.configAssertContains(authcfg, ['customauthzcode']):
            return None

        cfg = self.execCustomCode(authcfg["customauthzcode"], ['allowRules', 'roleMatchers'])
        return util.Authz(cfg['allowRules'], cfg['roleMatchers'])

    def createWorkerConfigWorker(self, config, name):
        return worker.Worker(name, password=config['password'])

    def createWorkerConfigLocalWorker(self, config, name):
        return worker.LocalWorker(name)

    def createWorkerConfigDockerWorker(self, config, name):
        return worker.DockerLatentWorker(name, str(uuid.uuid4()),
                                         docker_host=config['docker_host'], image=config['image'],
                                         followStartupLogs=True)

    def createWorkerConfig(self):
        self.config.setdefault('workers', [])
        if 'workers' not in self.cfgdict:
            return
        for _worker in self.cfgdict['workers']:
            createWorkerConfigMethod = 'createWorkerConfig' + _worker['type']

            if not hasattr(self, createWorkerConfigMethod):
                config_error("_worker type {} is not supported".format(_worker['type']))
                continue

            for i in xrange(_worker.get('number', 1)):
                name = _worker['name']
                if _worker.get('number', 1) != 1:
                    name = name + "_" + str(i + 1) # count one based
                self.config['workers'].append(getattr(self, createWorkerConfigMethod)(_worker, name))

    def fromDb(self):
        buildbot_travis.api.useDbConfig()
        dbConfig = util.DbConfig(self.config, self.vardir)
        return self.fromDict(dbConfig.get("travis", {}))

    def get_all_workers(self):
        workers = [s.workername for s in self.config[
            'workers']]
        return workers

    def get_spawner_workers(self):
        workers = [s.workername for s in self.config[
            'workers'] if not ILatentWorker.providedBy(s)]
        if not workers:
            return self.get_all_workers()
        return workers

    def get_runner_workers(self):
        workers = [s.workername for s in self.config[
            'workers'] if ILatentWorker.providedBy(s)]
        if not workers:
            return self.get_all_workers()
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
                                hide=False, required=False, size=20)

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
