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


class NotImportantFilesConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = this
        @$scope.title = "Not Important Files"

        @$scope.important_file_remove = (file) ->
            _.remove self.$scope.cfg.not_important_files, (i) -> i == file

        @$scope.important_file_add = ->
            if self.$scope.new_file
                self.$scope.cfg.not_important_files ?= []
                self.$scope.cfg.not_important_files.push(self.$scope.new_file)
                self.$scope.new_file = ""
