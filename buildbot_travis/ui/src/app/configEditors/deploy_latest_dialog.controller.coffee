class deployLatestDialog extends Controller
    constructor: ($scope, modal, commit, project, forcesched, buildername, config, $location) ->
        self = this
        self.$scope = $scope
        $scope.commit = commit
        $scope.project = project
        $scope.projectsDict = []

        # key = The key by which to index the dictionary
        Array::toDict = (key) ->
            @reduce ((dict, obj) -> dict[ obj[key] ] = obj if obj[key]?; return dict), {}


        # We need access to the deliverables names / stages / commit-description property
        @$scope.cfg = angular.copy(config.plugins.buildbot_travis.cfg)
        $scope.projectsDict = $scope.cfg.projects.toDict('name')

        # prepare default values
        prepareFields = (fields) ->
            for field in fields
                if field.fields?
                    prepareFields(field.fields)
                else
                    field.value = field.default
        prepareFields(forcesched.all_fields)
        angular.extend $scope,
            rootfield:
                type: 'nested'
                layout: 'simple'
                fields: forcesched.all_fields
                columns: 1
            sch: forcesched

        $scope.ok = (stage) ->
            params = {}
            gatherFields = (fields) ->
                for field in fields
                    field.errors = ''
                    if field.fields?
                        gatherFields(field.fields)
                    else
                        console.log field.fullName
                        if field.fullName.match(/revision/)
                            params[field.fullName] = commit
                        else if field.fullName == 'stage'
                            params[field.fullName] = stage
                        else
                            params[field.fullName] = field.value

            gatherFields(forcesched.all_fields)
            forcesched.control('force', params)
            .then (res) ->
                modal.modal.close(res.result)
            ,   (err) ->
                $scope.error = err.error.message

        $scope.cancel = ->
            modal.modal.dismiss()
