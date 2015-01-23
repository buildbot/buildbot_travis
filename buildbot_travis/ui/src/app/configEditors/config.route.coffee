# Register new state
class State extends Config
    constructor: ($stateProvider, glMenuServiceProvider) ->

        groupName = 'settings'

        # Configuration
        glMenuServiceProvider.addGroup
            name: groupName
            caption: 'Settings'
            icon: 'wrench'
            order: 150


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
