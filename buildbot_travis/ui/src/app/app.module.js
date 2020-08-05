// Register new module
class BuildbotTravis {
    constructor() { return [
        'common',
        'ui.bootstrap.showErrors',
        'ngTagsInput',
        'bbData'
    ]; }
}


angular.module('buildbot_travis', new BuildbotTravis());

require("./configEditors/directives/input-tags.directive.js");
require("./configEditors/directives/input_stages.directive.js");
require("./configEditors/directives/codeeditor.directive.js");
require("./configEditors/directives/configpage.directive.js");
require("./configEditors/deploydialog.controller.js");
require("./configEditors/deploy_latest_dialog.controller.js");
require("./configEditors/deploy.controller.js");
require("./configEditors/bbtravis_config.controller.js");
require("./configEditors/config.route.js");
require("angular-bootstrap-show-errors/src/showErrors.js");
require("ng-tags-input/build/ng-tags-input.js");
