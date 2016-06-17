class ProjectsConfig extends Controller
    self = null
    constructor: ($scope, config, $state) ->
        self = this
        self.$scope = $scope
        $scope.title = "Watched Projects"


        $scope.project_remove = (project) ->
            _.remove $scope.cfg.projects, (i) -> i == project

        $scope.shows = {}
        $scope.toggle_show = (i) ->
            $scope.shows[i] ?= false
            $scope.shows[i] = !$scope.shows[i]

        $scope.new_project = ->
            $scope.cfg.projects ?= []
            $scope.shows[$scope.cfg.projects.length] = true
            $scope.cfg.projects.push
                vcs_type: _.keys(config.plugins.buildbot_travis.supported_vcs)[0]

        $scope.is_shown = (i) ->
            return $scope.shows[i]

        $scope.allTags = (query) ->
            ret = []
            for p in $scope.cfg.projects
                if p.tags?
                    for tag in p.tags
                        if tag.indexOf(query) == 0 and ret.indexOf(tag) < 0
                            ret.push(tag)
            return ret

        $scope.allStages = (query) ->
            ret = []
            for s in $scope.cfg.stages
                if s.indexOf(query) == 0 and ret.indexOf(s) < 0
                    ret.push(s)
            return ret

        $scope.allBranches = (query) ->
            ret = []
            for p in $scope.cfg.projects
                if p.branches?
                    for b in p.branches
                        if b.indexOf(query) == 0 and ret.indexOf(b) < 0
                            ret.push(b)
            return ret

class EnvConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = this
        @$scope.title = "Default Environment Variables"
        @$scope.new_env = {}
        @$scope.env_remove = (key) ->
            delete $scope.cfg.env[key]

        @$scope.env_add = ->
            self.$scope.cfg.env ?= {}
            self.$scope.cfg.env[self.$scope.new_env.key] = self.$scope.new_env.value
            $scope.new_env = {}

class DeploymentConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = this
        @$scope.title = "Deployment Environments"
        @$scope.new_stage = ""

        @$scope.stage_remove = (stage) ->
            if self.$scope.cfg.stages.indexOf(stage) != -1
                self.$scope.cfg.stages.splice(self.$scope.cfg.stages.indexOf(stage), 1)

        @$scope.stage_add = (stage) ->
            if stage
                self.$scope.cfg.stages ?= []
                self.$scope.cfg.stages.push(stage)
                stage = ""

class NotImportantFilesConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = this
        @$scope.title = "Not Important Files"

        @$scope.important_file_remove = (file) ->
            _.remove self.$scope.cfg.workers, (i) -> i == file

        @$scope.important_file_add = ->
            if self.$scope.new_file
                self.$scope.cfg.workers ?= []
                self.$scope.cfg.not_important_files.push(self.$scope.new_file)
                self.$scope.new_file = ""



class WorkerConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = this
        @$scope.title = "Workers"
        @$scope.new_worker = type: "Worker"
        $scope.shows = {}

        $scope.toggle_show = (i) ->
            $scope.shows[i] ?= false
            $scope.shows[i] = !$scope.shows[i]

        $scope.is_shown = (i) ->
            return $scope.shows[i]

        @$scope.worker_remove = (worker) ->
            _.remove self.$scope.cfg.workers, (i) -> i == worker

        @$scope.worker_add = ->
            if self.$scope.new_worker.type
                self.$scope.cfg.workers ?= []
                name = "myslave" + (self.$scope.cfg.workers.length + 1).toString()
                $scope.shows[name] = true
                self.$scope.cfg.workers.push
                    name: name
                    type: self.$scope.new_worker.type
                    number: 1



DEFAULT_CUSTOM_AUTHCODE = """
from buildbot.plugins import *
auth = util.UserPasswordAuth({"homer": "doh!"})
"""
DEFAULT_CUSTOM_AUTHZCODE = """
from buildbot.plugins import *
from buildbot_travis.configurator import TravisEndpointMatcher
allowRules=[
    util.StopBuildEndpointMatcher(role="admins"),
    util.ForceBuildEndpointMatcher(role="admins"),
    util.RebuildBuildEndpointMatcher(role="admins"),
    TravisEndpointMatcher(role="admins")
]
roleMatchers=[
    util.RolesFromEmails(admins=["my@email.com"])
]
"""
class AuthConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = this
        @$scope.title = "Authentication and Authorization"
        @$scope.auth = {}
        @$scope.$watch "cfg", (cfg) ->
            if cfg
                cfg.auth ?= {type: "None"}
                self.$scope.auth = cfg.auth
        @$scope.$watch "auth.type", (type) ->
            if type == "Custom" and not self.$scope.auth.customcode
                self.$scope.auth.customcode = DEFAULT_CUSTOM_AUTHCODE
        @$scope.$watch "auth.authztype", (type) ->
            if type == "Groups" and not self.$scope.auth.groups
                self.$scope.auth.groups = []
            if type == "Emails" and not self.$scope.auth.emails
                self.$scope.auth.emails = []
            if type == "Custom" and not self.$scope.auth.customauthzcode
                self.$scope.auth.customauthzcode = DEFAULT_CUSTOM_AUTHZCODE
        @$scope.isOAuth = ->
            return self.$scope.auth.type in [ "Google", "GitLab", "GitHub"]
        @$scope.getOAuthDoc = (type) ->
            return {
                Google: "https://developers.google.com/accounts/docs/OAuth2"
                GitLab: "http://docs.gitlab.com/ce/api/oauth2.html"
                GitHub: "https://developer.github.com/v3/oauth/"
            }[type]
        @$scope.worker_add = ->
            if self.$scope.new_worker.type
                self.$scope.cfg.workers ?= []
                name = "myslave" + (self.$scope.cfg.workers.length + 1).toString()
                id = _.random(2 ** 32)
                $scope.shows[name] = true
                self.$scope.cfg.workers.push
                    name: name
                    type: self.$scope.new_worker.type
                    number: 1
