/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS205: Consider reworking code to avoid use of IIFEs
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class deployLatestDialog {
    constructor($scope, modal, commit, project, forcesched, buildername, config, $location) {
        const self = this;
        self.$scope = $scope;
        $scope.commit = commit;
        $scope.project = project;
        $scope.projectsDict = [];

        // key = The key by which to index the dictionary
        Array.prototype.toDict = function(key) {
            return this.reduce((function(dict, obj) { if (obj[key] != null) { dict[ obj[key] ] = obj; } return dict; }), {});
        };


        // We need access to the deliverables names / stages / commit-description property
        this.$scope.cfg = angular.copy(config.plugins.buildbot_travis.cfg);
        $scope.projectsDict = $scope.cfg.projects.toDict('name');

        // prepare default values
        var prepareFields = fields => Array.from(fields).map((field) =>
            (field.fields != null) ?
                prepareFields(field.fields)
            :
                (field.value = field.default));
        prepareFields(forcesched.all_fields);
        angular.extend($scope, {
            rootfield: {
                type: 'nested',
                layout: 'simple',
                fields: forcesched.all_fields,
                columns: 1
            },
            sch: forcesched
        }
        );

        $scope.ok = function(stage) {
            const params = {};
            var gatherFields = fields => (() => {
                const result = [];
                for (let field of Array.from(fields)) {
                    field.errors = '';
                    if (field.fields != null) {
                        result.push(gatherFields(field.fields));
                    } else {
                        if (field.fullName.match(/revision/)) {
                            result.push(params[field.fullName] = commit);
                        } else if (field.fullName === 'stage') {
                            result.push(params[field.fullName] = stage);
                        } else {
                            result.push(params[field.fullName] = field.value);
                        }
                    }
                }
                return result;
            })();

            gatherFields(forcesched.all_fields);
            return forcesched.control('force', params)
            .then(res => modal.modal.close(res.result)
            ,   err => $scope.error = err.error.message);
        };

        $scope.cancel = () => modal.modal.dismiss();
    }
}


angular.module('app')
.controller('deployLatestDialogController', ['$scope', 'modal', 'commit', 'project', 'forcesched', 'buildername', 'config', '$location', deployLatestDialog]);