# Register new module
class BuildbotTravis
    constructor: -> return [
        'common',
        'ui.bootstrap.showErrors',
        'ngTagsInput',
        'bbData'
    ]


angular.module('app', new BuildbotTravis())