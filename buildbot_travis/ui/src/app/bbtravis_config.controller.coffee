class ProjectsConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = @
        @$scope.title = "Watched Projects"
        @$scope.project_remove = (project) ->
            _.remove self.$scope.cfg.projects, (i) -> i == project

        @$scope.new_project = ->
            $scope.cfg.projects.push
                vcs_type: _.keys(config.plugins.buildbot_travis.supported_vcs)[0]

class EnvConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = @
        @$scope.title = "Default Environment Variables"
        $scope.new_env = {}
        @$scope.env_remove = (key) ->
            delete $scope.cfg.env[key]

        @$scope.env_add = ->
            self.$scope.cfg.env[self.$scope.new_env.key] = self.$scope.new_env.value
            $scope.new_env = {}

class NotImportantFilesConfig extends Controller
    self = null
    constructor: (@$scope, config, $state) ->
        self = @
        @$scope.title = "Not Important Files"

        @$scope.important_file_remove = (file) ->
            _.remove self.$scope.cfg.not_important_files, (i) -> i == file

        @$scope.important_file_add = ->
            if self.$scope.new_file
                self.$scope.cfg.not_important_files.push(self.$scope.new_file)
                self.$scope.new_file = ""
