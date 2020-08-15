// Register new state
class State {
    constructor($stateProvider, glMenuServiceProvider) {


        let groupName = 'deploy dashboard';

        // Configuration
        glMenuServiceProvider.addGroup({
            name: groupName,
            caption: 'Deploy',
            icon: 'rocket',
            order: 0
        });


        // Register new state
        $stateProvider.state({
            controller: "deployController",
            template: require("./deploy.tpl.jade"),
            name: "travis_deploy",
            url: "/bbtravis/deploy",
            data: {
                group: groupName,
                caption: 'Deploy'
            }
        });

        groupName = 'administration';

        // Configuration
        glMenuServiceProvider.addGroup({
            name: groupName,
            caption: 'Administration',
            icon: 'wrench',
            order: 150
        });

        // Register new state for Deployment settings section
        $stateProvider.state({
            controller: "deploymentConfigController",
            template: require("./deployment.tpl.jade"),
            name: "travis_config_deployment",
            url: "/bbtravis/config/deployment",
            data: {
                group: groupName,
                caption: 'Deployment'
            }
        });

        // Register new state
        $stateProvider.state({
            controller: "projectsConfigController",
            template: require("./projects.tpl.jade"),
            name: "travis_config_projects",
            url: "/bbtravis/config/projects",
            data: {
                group: groupName,
                caption: 'Projects'
            }
        });

        // Register new state
        $stateProvider.state({
            controller: "envConfigController",
            template: require("./env.tpl.jade"),
            name: "travis_config_env",
            url: "/bbtravis/config/env",
            data: {
                group: groupName,
                caption: 'Environment variables'
            }
        });

        // Register new state
        $stateProvider.state({
            controller: "notImportantFilesConfigController",
            template: require("./not_important_files.tpl.jade"),
            name: "not_important_files",
            url: "/bbtravis/config/not_important_files",
            data: {
                group: groupName,
                caption: 'Not Important Files'
            }
        });

        // Register new state
        $stateProvider.state({
            controller: "workerConfigController",
            template: require("./workers_config.tpl.jade"),
            name: "workers_config",
            url: "/bbtravis/config/workers",
            data: {
                group: groupName,
                caption: 'Workers'
            }
        });

        // Register new state
        $stateProvider.state({
            controller: "authConfigController",
            template: require("./auth.tpl.jade"),
            name: "auth_config",
            url: "/bbtravis/config/auth",
            data: {
                group: groupName,
                caption: 'Authentication'
            }
        });
    }
}


angular.module('app')
.config(['$stateProvider', 'glMenuServiceProvider', State]);