class InputStages extends Directive
    constructor: ->
        return {
            replace: false
            transclude: false
            restrict: 'E' # E: Element
            scope: {allStages: '=', stages: '=', placeholder:"@"}
            templateUrl: 'buildbot_travis/views/input_stages.html'
            controller: '_InputStagesController'
        }


class _InputStages extends Controller
    self = null
    constructor: ($scope) ->
        self = this
        $scope.stages_model = []
        $scope.stages ?= []
        for t in $scope.stages
            if angular.isObject(t)
                t = t.text
            $scope.stages_model.push(text:t)

        updateStages = ->
            $scope.stages.splice(0, $scope.stages.length)
            for t in $scope.stages_model
                $scope.stages_model.push(t.text)
        updateStages()
        $scope.$watch("stages_model", updateStages, true)
