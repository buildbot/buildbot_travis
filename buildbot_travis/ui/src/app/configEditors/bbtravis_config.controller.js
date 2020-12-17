/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
var ProjectsConfig = (function() {
    let self = undefined;
    ProjectsConfig = class ProjectsConfig {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state) {
            self = this;
            self.$scope = $scope;
            $scope.title = "Watched Projects";


            $scope.project_remove = project => _.remove($scope.cfg.projects, i => i === project);

            $scope.shows = {};
            $scope.toggle_show = function(i) {
                if ($scope.shows[i] == null) { $scope.shows[i] = false; }
                return $scope.shows[i] = !$scope.shows[i];
            };

            $scope.new_project = function() {
                if ($scope.cfg.projects == null) { $scope.cfg.projects = []; }
                $scope.shows[$scope.cfg.projects.length] = true;
                return $scope.cfg.projects.push({
                    vcs_type: _.keys(config.plugins.buildbot_travis.supported_vcs)[0]});
            };

            $scope.is_shown = i => $scope.shows[i];

            $scope.allTags = function(query) {
                const ret = [];
                for (let p of Array.from($scope.cfg.projects)) {
                    if (p.tags != null) {
                        for (let tag of Array.from(p.tags)) {
                            if ((tag.indexOf(query) === 0) && (ret.indexOf(tag) < 0)) {
                                ret.push(tag);
                            }
                        }
                    }
                }
                return ret;
            };

            $scope.allStages = function(query) {
                const ret = [];
                for (let s of Array.from($scope.cfg.stages)) {
                    if ((s.indexOf(query) === 0) && (ret.indexOf(s) < 0)) {
                        ret.push(s);
                    }
                }
                return ret;
            };

            $scope.allBranches = function(query) {
                const ret = [];
                for (let p of Array.from($scope.cfg.projects)) {
                    if (p.branches != null) {
                        for (let b of Array.from(p.branches)) {
                            if ((b.indexOf(query) === 0) && (ret.indexOf(b) < 0)) {
                                ret.push(b);
                            }
                        }
                    }
                }
                return ret;
            };
        }
    };
    ProjectsConfig.initClass();
    return ProjectsConfig;
})();

var EnvConfig = (function() {
    let self = undefined;
    EnvConfig = class EnvConfig {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state) {
            this.$scope = $scope;
            self = this;
            this.$scope.title = "Default Environment Variables";
            this.$scope.new_env = {};
            this.$scope.env_remove = key => delete $scope.cfg.env[key];

            this.$scope.env_add = function() {
                if (self.$scope.cfg.env == null) { self.$scope.cfg.env = {}; }
                self.$scope.cfg.env[self.$scope.new_env.key] = self.$scope.new_env.value;
                return $scope.new_env = {};
            };
        }
    };
    EnvConfig.initClass();
    return EnvConfig;
})();

var DeploymentConfig = (function() {
    let self = undefined;
    DeploymentConfig = class DeploymentConfig {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state) {
            this.$scope = $scope;
            self = this;
            this.$scope.title = "Deployment Environments";
            this.$scope.new_stage = "";

            this.$scope.stage_remove = function(stage) {
                if (self.$scope.cfg.stages.indexOf(stage) !== -1) {
                    return self.$scope.cfg.stages.splice(self.$scope.cfg.stages.indexOf(stage), 1);
                }
            };

            this.$scope.stage_add = function(stage) {
                if (stage) {
                    if (self.$scope.cfg.stages == null) { self.$scope.cfg.stages = []; }
                    self.$scope.cfg.stages.push(stage);
                    return stage = "";
                }
            };
        }
    };
    DeploymentConfig.initClass();
    return DeploymentConfig;
})();

var NotImportantFilesConfig = (function() {
    let self = undefined;
    NotImportantFilesConfig = class NotImportantFilesConfig {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state) {
            this.$scope = $scope;
            self = this;
            this.$scope.title = "Not Important Files";

            this.$scope.important_file_remove = file => _.remove(self.$scope.cfg.workers, i => i === file);

            this.$scope.important_file_add = function() {
                if (self.$scope.new_file) {
                    if (self.$scope.cfg.workers == null) { self.$scope.cfg.workers = []; }
                    self.$scope.cfg.not_important_files.push(self.$scope.new_file);
                    return self.$scope.new_file = "";
                }
            };
        }
    };
    NotImportantFilesConfig.initClass();
    return NotImportantFilesConfig;
})();



var WorkerConfig = (function() {
    let self = undefined;
    WorkerConfig = class WorkerConfig {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state) {
            this.$scope = $scope;
            self = this;
            this.$scope.title = "Workers";
            this.$scope.new_worker = {type: "Worker"};
            this.$scope.shows = {};

            this.$scope.toggle_show = function(i) {
                if (self.$scope.shows[i] == null) { self.$scope.shows[i] = false; }
                return self.$scope.shows[i] = !self.$scope.shows[i];
            };

            this.$scope.is_shown = i => self.$scope.shows[i];

            this.$scope.worker_remove = worker => _.remove(self.$scope.cfg.workers, i => i === worker);

            this.$scope.worker_add = function() {
                if (self.$scope.new_worker.type) {
                    if (self.$scope.cfg.workers == null) { self.$scope.cfg.workers = []; }
                    const name = "myworker" + (self.$scope.cfg.workers.length + 1).toString();
                    const id = _.random(Math.pow(2, 32));
                    self.$scope.shows[name] = true;
                    self.$scope.cfg.workers.push({
                        name,
                        type: self.$scope.new_worker.type,
                        number: 1,
                        id
                    });
                    return self.$scope.toggle_show(id);
                }
            };
        }
    };
    WorkerConfig.initClass();
    return WorkerConfig;
})();


const DEFAULT_CUSTOM_AUTHCODE = `\
from buildbot.plugins import *
auth = util.UserPasswordAuth({"homer": "doh!"})\
`;
const DEFAULT_CUSTOM_AUTHZCODE = `\
from buildbot.plugins import *
from buildbot_travis.configurator import TravisEndpointMatcher
allowRules=[
    util.StopBuildEndpointMatcher(role="admins"),
    util.ForceBuildEndpointMatcher(role="admins"),
    util.RebuildBuildEndpointMatcher(role="admins"),
    TravisEndpointMatcher(role="admins")
]
roleMatchers=[
    util.RolesFromEmails(admins=["my@email.com"])
]\
`;
var AuthConfig = (function() {
    let self = undefined;
    AuthConfig = class AuthConfig {
        static initClass() {
            self = null;
        }
        constructor($scope, config, $state) {
            this.$scope = $scope;
            self = this;
            this.$scope.title = "Authentication and Authorization";
            this.$scope.auth = {};
            this.$scope.$watch("cfg", function(cfg) {
                if (cfg) {
                    if (cfg.auth == null) { cfg.auth = {type: "None"}; }
                    return self.$scope.auth = cfg.auth;
                }
            });
            this.$scope.$watch("auth.type", function(type) {
                if ((type === "Custom") && !self.$scope.auth.customcode) {
                    return self.$scope.auth.customcode = DEFAULT_CUSTOM_AUTHCODE;
                }
            });
            this.$scope.$watch("auth.authztype", function(type) {
                if ((type === "Groups") && !self.$scope.auth.groups) {
                    self.$scope.auth.groups = [];
                }
                if ((type === "Emails") && !self.$scope.auth.emails) {
                    self.$scope.auth.emails = [];
                }
                if ((type === "Custom") && !self.$scope.auth.customauthzcode) {
                    return self.$scope.auth.customauthzcode = DEFAULT_CUSTOM_AUTHZCODE;
                }
            });
            this.$scope.isOAuth = () => [ "Google", "GitLab", "GitHub", "Bitbucket"].includes(self.$scope.auth.type);
            this.$scope.getOAuthDoc = type => ({
                Google: "https://developers.google.com/accounts/docs/OAuth2",
                GitLab: "http://docs.gitlab.com/ce/api/oauth2.html",
                GitHub: "https://developer.github.com/v3/oauth/",
                Bitbucket: "https://confluence.atlassian.com/bitbucket/oauth-on-bitbucket-cloud-238027431.html"
            })[type];
        }
    };
    AuthConfig.initClass();
    return AuthConfig;
})();


angular.module('app')
.controller('projectsConfigController', ['$scope', 'config', '$state', ProjectsConfig])
.controller('envConfigController', ['$scope', 'config', '$state', EnvConfig])
.controller('deploymentConfigController', ['$scope', 'config', '$state', DeploymentConfig])
.controller('notImportantFilesConfigController', ['$scope', 'config', '$state', NotImportantFilesConfig])
.controller('workerConfigController', ['$scope', 'config', '$state', WorkerConfig])
.controller('authConfigController', ['$scope', 'config', '$state', AuthConfig]);