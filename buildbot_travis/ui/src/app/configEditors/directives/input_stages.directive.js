/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS205: Consider reworking code to avoid use of IIFEs
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class InputStages {
    constructor() {
        return {
            replace: false,
            transclude: false,
            restrict: 'E', // E: Element
            scope: {allStages: '=', stages: '=', placeholder:"@"},
            template: require('./input_stages.tpl.jade'),
            controller: '_InputStagesController'
        };
    }
}


var _InputStages = (function() {
    let self = undefined;
    _InputStages = class _InputStages {
        static initClass() {
            self = null;
        }
        constructor($scope) {
            let t;
            self = this;
            $scope.stages_model = [];
            if ($scope.stages == null) { $scope.stages = []; }
            for (t of Array.from($scope.stages)) {
                if (angular.isObject(t)) {
                    t = t.text;
                }
                $scope.stages_model.push({text:t});
            }

            const updateStages = function() {
                $scope.stages.splice(0, $scope.stages.length);
                return (() => {
                    const result = [];
                    for (t of Array.from($scope.stages_model)) {
                        result.push($scope.stages_model.push(t.text));
                    }
                    return result;
                })();
            };
            updateStages();
            $scope.$watch("stages_model", updateStages, true);
        }
    };
    _InputStages.initClass();
    return _InputStages;
})();


angular.module('app')
.directive('inputStages', [InputStages])
.controller('_InputStagesController', ['$scope', _InputStages]);