/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS205: Consider reworking code to avoid use of IIFEs
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class ConfigPage {
    constructor() {
        return {
            replace: true,
            transclude: true,
            restrict: 'E', // E: Element
            template: require('./config_page.tpl.jade'),
            controller: '_ConfigPageController'
        };
    }
}


var _ConfigPage = (function() {
    let self = undefined;
    _ConfigPage = class _ConfigPage {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state, $http) {
            this.$scope = $scope;
            self = this;
            this.$scope.loading = true;
            $http.get("buildbot_travis/api/config").then(function(travis_config) {
                travis_config = travis_config.data;
                self.$scope.loading = false;
                self.$scope.forbidden = false;
                self.$scope.original_cfg = travis_config;
                self.$scope.cfg = angular.copy(travis_config);
                return (() => {
                    const result = [];
                    for (let p of Array.from(self.$scope.cfg.projects)) {
                        if (p.branch) {
                            p.branches = p.branch.split(" ");
                            result.push(delete p.branch);
                        } else {
                            result.push(undefined);
                        }
                    }
                    return result;
                })();
            }
            , function() {
                self.$scope.loading = false;
                return self.$scope.forbidden = true;
            });
            this.$scope.buildbot_travis = config.plugins.buildbot_travis;
            this.$scope.errors = [];
            this.$scope.saving = false;
            this.$scope.save = function() {
                self.$scope.$broadcast('show-errors-check-validity');
                if (!self.$scope.hasInvalids()) {
                    self.$scope.original_cfg = angular.copy(self.$scope.cfg);
                    self.$scope.saving = true;
                    return $http.put("buildbot_travis/api/config", self.$scope.original_cfg).then(function(res) {
                        if (res.data.success) {
                            return location.reload(true);  // reload the application to take in account new builders
                        } else {
                            self.$scope.saving = false;
                            return self.$scope.errors = res.data.errors;
                        }
                    });
                }
            };


            this.$scope.cancel = function() {
                return this.$scope.cfg = angular.copy(this.$scope.original_cfg);
            };

            this.$scope.hasInvalids = function() {
                var hasInvalidInScope = function(scope) {
                    if (scope.form != null ? scope.form.$invalid : undefined) {
                        return true;
                    }
                    let cs = scope.$$childHead;
                    while (cs) {
                        if (hasInvalidInScope(cs)) {
                            return true;
                        }
                        cs = cs.$$nextSibling;
                    }
                    return false;
                };
                const ret = hasInvalidInScope(self.$scope);
                return ret;
            };
        }
    };
    _ConfigPage.initClass();
    return _ConfigPage;
})();


angular.module('app')
.directive('configPage', [ConfigPage])
.controller('_ConfigPageController', ['$scope', 'config', '$state', '$http', _ConfigPage]);