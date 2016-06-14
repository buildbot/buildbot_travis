# Register new state
class State extends Config
    constructor: ($stateProvider, glMenuServiceProvider) ->


        groupName = 'deploy dashboard'

        # Configuration
        glMenuServiceProvider.addGroup
            name: groupName
            caption: 'Deploy'
            icon: 'rocket'
            order: 0


        # Register new state
        $stateProvider.state
            controller: "deployController"
            templateUrl: "buildbot_travis/views/deploy.html"
            name: "travis_deploy"
            url: "/bbtravis/deploy"
            data:
                group: groupName
                caption: 'Deploy'

        groupName = 'settings'

        # Configuration
        glMenuServiceProvider.addGroup
            name: groupName
            caption: 'Settings'
            icon: 'wrench'
            order: 150

        # Register new state for Deployment settings section
        $stateProvider.state
            controller: "deploymentConfigController"
            templateUrl: "buildbot_travis/views/deployment.html"
            name: "travis_config_deployment"
            url: "/bbtravis/config/deployment"
            data:
                group: groupName
                caption: 'Deployment'

        # Register new state
        $stateProvider.state
            controller: "projectsConfigController"
            templateUrl: "buildbot_travis/views/projects.html"
            name: "travis_config_projects"
            url: "/bbtravis/config/projects"
            data:
                group: groupName
                caption: 'Projects'

        # Register new state
        $stateProvider.state
            controller: "envConfigController"
            templateUrl: "buildbot_travis/views/env.html"
            name: "travis_config_env"
            url: "/bbtravis/config/env"
            data:
                group: groupName
                caption: 'Environment variables'

        # Register new state
        $stateProvider.state
            controller: "notImportantFilesConfigController"
            templateUrl: "buildbot_travis/views/not_important_files.html"
            name: "not_important_files"
            url: "/bbtravis/config/not_important_files"
            data:
                group: groupName
                caption: 'Not Important Files'

        # Register new state
        $stateProvider.state
            controller: "workerConfigController"
            templateUrl: "buildbot_travis/views/workers_config.html"
            name: "workers_config"
            url: "/bbtravis/config/workers"
            data:
                group: groupName
                caption: 'Workers'

        # Register new state
        $stateProvider.state
            controller: "authConfigController"
            templateUrl: "buildbot_travis/views/auth.html"
            name: "auth_config"
            url: "/bbtravis/config/auth"
            data:
                group: groupName
                caption: 'Authentication'
