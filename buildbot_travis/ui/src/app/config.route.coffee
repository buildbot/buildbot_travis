# Register new state
class State extends Config
    constructor: ($stateProvider, glMenuServiceProvider) ->

        # Name of the state
        name = 'travis_config'

        # Configuration
        glMenuServiceProvider.addGroup
            name: name
            caption: 'BuildbotTravis Config'
            icon: 'wrench'
            order: 150


        # Register new state
        $stateProvider.state
            controller: "projectsConfigController"
            templateUrl: "buildbot_travis/views/projects.html"
            name: "travis_config_projects"
            url: "/bbtravis/config/projects"
            data:
                group: name
                caption: 'Projects'

        # Register new state
        $stateProvider.state
            controller: "envConfigController"
            templateUrl: "buildbot_travis/views/env.html"
            name: "travis_config_env"
            url: "/bbtravis/config/env"
            data:
                group: name
                caption: 'Environment variables'

        # Register new state
        $stateProvider.state
            controller: "notImportantFilesConfigController"
            templateUrl: "buildbot_travis/views/not_important_files.html"
            name: "not_important_files"
            url: "/bbtravis/config/not_important_files"
            data:
                group: name
                caption: 'Not Important Files'
