class ConfigPage
    constructor: ->
        return {
            replace: true
            transclude: true
            restrict: 'E' # E: Element
            templateUrl: 'buildbot_travis/views/config_page.html'
            controller: '_ConfigPageController'
        }


class _ConfigPage
    self = null
    constructor: (@$scope, config, $state, $http) ->
        self = this
        @$scope.loading = true
        $http.get("buildbot_travis/api/config").then (travis_config) ->
            travis_config = travis_config.data
            self.$scope.loading = false
            self.$scope.forbidden = false
            self.$scope.original_cfg = travis_config
            self.$scope.cfg = angular.copy(travis_config)
            for p in self.$scope.cfg.projects
                if p.branch
                    p.branches = p.branch.split(" ")
                    delete p.branch
        , ->
            self.$scope.loading = false
            self.$scope.forbidden = true
        @$scope.buildbot_travis = config.plugins.buildbot_travis
        @$scope.errors = []
        @$scope.saving = false
        @$scope.save = ->
            self.$scope.$broadcast('show-errors-check-validity')
            if not self.$scope.hasInvalids()
                self.$scope.original_cfg = angular.copy(self.$scope.cfg)
                self.$scope.saving = true
                $http.put("buildbot_travis/api/config", self.$scope.original_cfg).then (res) ->
                    if res.data.success
                        location.reload(true)  # reload the application to take in account new builders
                    else
                        self.$scope.saving = false
                        self.$scope.errors = res.data.errors


        @$scope.cancel = ->
            @$scope.cfg = angular.copy(@$scope.original_cfg)

        @$scope.hasInvalids = ->
            hasInvalidInScope = (scope) ->
                if scope.form?.$invalid
                    return true
                cs = scope.$$childHead
                while cs
                    if hasInvalidInScope(cs)
                        return true
                    cs = cs.$$nextSibling
                return false
            ret = hasInvalidInScope(self.$scope)
            return ret


angular.module('app')
.directive('configPage', [ConfigPage])
.controller('_ConfigPageController', ['$scope', 'config', '$state', '$http', _ConfigPage])