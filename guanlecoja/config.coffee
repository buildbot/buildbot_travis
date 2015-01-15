### ###############################################################################################
#
#   This module contains all configuration for the build process
#
### ###############################################################################################
basedir = "buildbot_travis/ui/"
module.exports =

    ### ###########################################################################################
    #   Directories
    ### ###########################################################################################
    name: 'buildbot_travis' # set default module name
    dir: build: 'buildbot_travis/static'
    files:
        # app entrypoint should be placed first, so need to be specific
        app: [
            basedir + 'src/**/*.module.coffee'
        ]

        # scripts (can be coffee or js)
        scripts: [
            basedir + 'src/**/*.coffee'
            "!#{basedir}src/**/*.spec.coffee"
        ]

        # CoffeeScript tests
        tests: [
            basedir + 'test/**/*.coffee'
            basedir + 'src/**/*.spec.coffee'
        ]

        # fixtures
        fixtures: [
            basedir + 'test/**/*.fixture.*'
            basedir + 'src/**/*.fixture.*'
        ]

        # Jade templates
        templates: [
            basedir + 'src/**/*.tpl.jade'
        ]

        # Less stylesheets
        less: [
            basedir + 'src/**/*.less'
        ]

        # Images
        images: [
            basedir + 'src/**/*.{png,jpg,gif,ico}'
        ]
    bower:
        directory: basedir + "libs"
        # JavaScript libraries
        deps:
            "angular-bootstrap-show-errors":
                version: "~2.2.0"
                files: "src/showErrors.js"
        testdeps:
            angular:
                version: "~1.3.0"
                files: 'angular.js'
            lodash:
                version: "~2.4.1"
                files: 'dist/lodash.js'
            "angular-mocks":
                version: "~1.3.0"
                files: "angular-mocks.js"
    karma:
        # we put tests first, so that we have angular, and fake app defined
        files: ["tests.js", "scripts.js", 'fixtures.js', "mode-python.js"]
