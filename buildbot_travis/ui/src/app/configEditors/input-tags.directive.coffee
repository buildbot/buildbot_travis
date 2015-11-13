class InputTags extends Directive
    constructor: ->
        return {
            replace: false
            transclude: false
            restrict: 'E' # E: Element
            scope: {allTags: '=', tags: '=', placeholder:"@"}
            templateUrl: 'buildbot_travis/views/input_tags.html'
            controller: '_InputTagsController'
        }


class _InputTags extends Controller
    self = null
    constructor: ($scope) ->
        self = this
        $scope.tags_model = []
        $scope.tags ?= []
        for t in $scope.tags
            if angular.isObject(t)
                t = t.text
            $scope.tags_model.push(text:t)

        updateTags = ->
            $scope.tags.splice(0, $scope.tags.length)
            for t in $scope.tags_model
                $scope.tags.push(t.text)
        updateTags()
        $scope.$watch("tags_model", updateTags, true)
