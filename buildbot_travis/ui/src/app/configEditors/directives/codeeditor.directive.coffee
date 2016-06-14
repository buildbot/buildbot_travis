# a simple directive which lazy-loads ace from the cdn
# if it fails, it will just use a textarea
# ace is not embedded by default as it is huge

# if ace load is failed (because of closed network), then we still have the textarea as a fallback

ace_injected = false

class CodeEditor extends Directive
    constructor: ->
        return {
            replace: false
            transclude: false
            restrict: 'E'
            scope: {code: '='}
            templateUrl: 'buildbot_travis/views/codeeditor.html'
            controller: '_CodeEditorController'
        }
class _CodeEditor extends Controller
    self = null
    constructor: ($scope) ->
        self = this
        if ace_injected == false
            ace_injected =
                $.getScript("https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.3/ace.js")

        ace_injected.then ->
            editor = window.ace.edit("codeeditor")
            editor.setOptions maxLines: Infinity
            editor.$blockScrolling = Infinity
            editor.getSession().setMode("ace/mode/python")
            if $scope.code?
                editor.setValue($scope.code, -1)
            editor.getSession().on 'change',
                _.debounce -> # make sure we add a small delay in order not to delay to much.
                    $scope.$apply ->
                        $scope.code = editor.getValue()
                , 200
            $scope.$on "$destroy", ->
                editor.destroy()
