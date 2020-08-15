/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
// a simple directive which lazy-loads ace from the cdn
// if it fails, it will just use a textarea
// ace is not embedded by default as it is huge

// if ace load is failed (because of closed network), then we still have the textarea as a fallback

let ace_injected = false;

class CodeEditor {
    constructor() {
        return {
            replace: false,
            transclude: false,
            restrict: 'E',
            scope: {code: '='},
            template: require("./codeeditor.tpl.jade"),
            controller: '_CodeEditorController'
        };
    }
}
var _CodeEditor = (function() {
    let self = undefined;
    _CodeEditor = class _CodeEditor {
        static initClass() {
            self = null;
        }
        constructor($scope) {
            self = this;
            if (ace_injected === false) {
                ace_injected =
                    $.getScript("https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.3/ace.js");
            }

            ace_injected.then(function() {
                const editor = window.ace.edit("codeeditor");
                editor.setOptions({maxLines: Infinity});
                editor.$blockScrolling = Infinity;
                editor.getSession().setMode("ace/mode/python");
                if ($scope.code != null) {
                    editor.setValue($scope.code, -1);
                }
                editor.getSession().on('change',
                    _.debounce(() => // make sure we add a small delay in order not to delay to much.
                    $scope.$apply(() => $scope.code = editor.getValue())
                    , 200)
                );
                return $scope.$on("$destroy", () => editor.destroy());
            });
        }
    };
    _CodeEditor.initClass();
    return _CodeEditor;
})();


angular.module('app')
.directive('codeEditor', [CodeEditor])
.controller('_CodeEditorController', ['$scope', _CodeEditor]);