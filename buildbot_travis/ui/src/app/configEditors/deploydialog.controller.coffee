class deployDialog extends Controller
    constructor: ($scope, modal, tag, project, stage, forcesched, buildername) ->
        $scope.tag = tag
        $scope.project = project
        $scope.stage = stage

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

        $scope.ok = ->
            params = {}
            gatherFields = (fields) ->
                for field in fields
                    field.errors = ''
                    if field.fields?
                        gatherFields(field.fields)
                    else
                        if field.fullName == 'version'
                            params[field.fullName] = tag
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
