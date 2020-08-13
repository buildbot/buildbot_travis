/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS205: Consider reworking code to avoid use of IIFEs
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class deployDialog {
    constructor($scope, modal, tag, project, stage, forcesched, buildername) {
        $scope.tag = tag;
        $scope.project = project;
        $scope.stage = stage;

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

        $scope.ok = function() {
            const params = {};
            var gatherFields = fields => (() => {
                const result = [];
                for (let field of Array.from(fields)) {
                    field.errors = '';
                    if (field.fields != null) {
                        result.push(gatherFields(field.fields));
                    } else {
                        if (field.fullName === 'version') {
                            result.push(params[field.fullName] = tag);
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
.controller('deployDialogController', ['$scope', 'modal', 'tag', 'project', 'stage', 'forcesched', 'buildername', deployDialog]);