/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS205: Consider reworking code to avoid use of IIFEs
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class InputTags {
    constructor() {
        return {
            replace: false,
            transclude: false,
            restrict: 'E', // E: Element
            scope: {allTags: '=?', tags: '=', placeholder:"@"},
            templateUrl: 'buildbot_travis/views/input_tags.html',
            controller: '_InputTagsController'
        };
    }
}


var _InputTags = (function() {
    let self = undefined;
    _InputTags = class _InputTags {
        static initClass() {
            self = null;
        }
        constructor($scope) {
            let t;
            self = this;
            $scope.tags_model = [];
            if ($scope.tags == null) { $scope.tags = []; }
            if ($scope.allTags == null) { $scope.allTags = () => []; }
            for (t of Array.from($scope.tags)) {
                if (angular.isObject(t)) {
                    t = t.text;
                }
                $scope.tags_model.push({text:t});
            }

            const updateTags = function() {
                $scope.tags.splice(0, $scope.tags.length);
                return (() => {
                    const result = [];
                    for (t of Array.from($scope.tags_model)) {
                        result.push($scope.tags.push(t.text));
                    }
                    return result;
                })();
            };
            updateTags();
            $scope.$watch("tags_model", updateTags, true);
        }
    };
    _InputTags.initClass();
    return _InputTags;
})();


angular.module('app')
.directive('inputTags', [InputTags])
.controller('_InputTagsController', ['$scope', _InputTags]);