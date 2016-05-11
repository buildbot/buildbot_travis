class Deploy extends Controller
    self = null
    constructor: ($scope, $state, $uibModal, config, dataService) ->
        self = this
        self.$scope = $scope
        $scope.title = 'Deployment info'
        $scope.fscheduler = ''
        $scope.builderName = ''
        $scope.latestDeployedVersionByProjectDict = {}
        $scope.gitTagsByProjectDict = {}
        $scope.untaggedVersionsByProject = []
        $scope.untaggedVersionsByProjectDict = {}
        $scope.projectsFiltered = []
        latestDeployedVersionByProject = []
        gitTagsByProject = []
        data = []

        # We need access to the deliverables names / stages / GIT tags / commit-description property
        @$scope.cfg = angular.copy(config.plugins.buildbot_travis.cfg)

        # Automatically closes all the bindings when the $scope is destroyed
        data = dataService.open().closeOnDestroy($scope)

        # key = The key by which to index the dictionary
        Array::toDict = (key) ->
            @reduce ((dict, obj) -> dict[ obj[key] ] = obj if obj[key]?; return dict), {}

        filterProjects = ->
            console.log 'Filtering projects ...'
            for p in $scope.cfg.projects
                if p.stages? and p.stages.length > 0
                    $scope.projectsFiltered.push(p)


        initVersions = ->
            console.log 'Initializing the versions ...'
            for p in $scope.projectsFiltered
                latestDeployedVersion = {}
                latestDeployedVersion.projectName = p.name
                latestDeployedVersion.stages_sorted = {}
                latestDeployedVersion.stages = []
                for s in p.stages
                    depInfo = {}
                    depInfo.stage = ''
                    depInfo.versions = []
                    depInfo.versions = ['NA']
                    depInfo.stage = s
                    latestDeployedVersion.stages.push(depInfo)
                latestDeployedVersionByProject.push(latestDeployedVersion)
                projGitTag = {}
                projGitTag.projectName = p.name
                projGitTag.projectGitTags = ['NA']
                gitTagsByProject.push(projGitTag)
                projVersion = {}
                projVersion.projectName = p.name
                projVersion.versions = []
                $scope.untaggedVersionsByProject.push(projVersion)

            $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName')
            $scope.gitTagsByProjectDict = gitTagsByProject.toDict('projectName')
            $scope.untaggedVersionsByProjectDict = $scope.untaggedVersionsByProject.toDict('projectName')
            projectsDict = $scope.cfg.projects.toDict('name')


        $scope.isStageUndefined = (project, stage)->
            if $scope.projectsDict[project].stages?
                if stage in $scope.projectsDict[project].stages
                    return false
                else
                    return true
            else
                return true

        retrieveInfo = ->
            # Retrieve the commit-description properties that contain ALL the versions (tagged or not)
            # First case : dev have been successfully merged, ready to be deployed in 'post commit' stages - not GIT tagged yet
            # Second case : dev have been deployed in 'post commit' stages - GIT tagged
            data.getBuilders().onNew = (builder) ->
                console.log 'Retrieving the builders'
                name = ''
                name = builder.name

                for p, k in $scope.projectsFiltered

                    if name.match(p.name)
                        if not name.match(/-deploy/) and not name.match(/-job/) and not name.match(/-try/)
                            data.getBuilds(limit: 50, order: '-complete_at', builderid: builder.builderid, complete: 'true', results: 0).onChange = (builds) ->
                                console.log 'Retrieving the builds...'
                                for build in builds
                                    build.getProperties().onNew = (properties) ->
                                        if properties['branch']?
                                            # NOT GIT tagged versions - 'post-commit' stages candidates
                                            if not properties['branch'][0].match(/tags/)
                                                projectName = properties['codebase'][0]

                                                if properties['revision']?

                                                    for version in $scope.untaggedVersionsByProject
                                                        if projectName == version.projectName
                                                            if properties['revision'][0] not in version.versions
                                                                new_version = properties['revision'][0]
                                                                version.versions.push(new_version)
                                                    $scope.untaggedVersionsByProjectDict = $scope.untaggedVersionsByProject.toDict('projectName')

                                            # GIT tagged versions
                                            if properties['branch'][0].match(/tags/)
                                                projectName = properties['codebase'][0]
                                                if properties['commit-description']?
                                                    for g in gitTagsByProject
                                                       if projectName == g.projectName
                                                            if properties['commit-description'][0] not in g.projectGitTags
                                                                new_version = []
                                                                new_version = properties['commit-description'][0]
                                                                if g.projectGitTags[0] == 'NA'
                                                                    g.projectGitTags = []
                                                                if new_version[projectName] not in g.projectGitTags
                                                                    g.projectGitTags.push(new_version[projectName])
                                                    $scope.gitTagsByProjectDict = gitTagsByProject.toDict('projectName')

                        else if name.match(/-deploy/)
                            data.getBuilds(limit: 50, order: '-complete_at', builderid: builder.builderid, complete: 'true', results: 0).onChange = (builds) ->
                                console.log 'Retrieving the deploy builds...'
                                for build in builds
                                    build.getProperties().onNew = (properties) ->
                                        if properties?
                                            projectName = properties['codebase'][0]

                                            if properties['version'][0]? and properties['version'][0] != ''
                                                if properties['stage'][0]? and properties['stage'][0] != ''
                                                    if latestDeployedVersionByProject != []
                                                        for p in latestDeployedVersionByProject
                                                            if p.projectName == projectName
                                                                for s in p.stages
                                                                    if s.stage == properties['stage'][0]
                                                                        if s.versions[0] == 'NA'
                                                                            s.versions = []
                                                                            s.versions.push(properties['version'][0])
                                                                        else
                                                                            new_version = properties['version'][0]
                                                                            if new_version not in s.versions
                                                                                s.versions.push(properties['version'][0])
                                                                stage_info = {}
                                                                stage_info = p.stages.toDict('stage')
                                                                p.stages_sorted = stage_info
                                                        $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName')



                        else
                            return


        filterProjects()
        initVersions()

        retrieveInfo()

        $scope.submit = ->
            console.log $scope.selectedTag
            console.log $scope.selectedProject
            console.log $scope.selectedStage
            console.log $scope.builderName


        $scope.deploy = (tag, project, stage) ->
            $scope.selectedTag = tag
            $scope.selectedProject = project
            $scope.selectedStage = stage

            fschedulerName = $scope.selectedProject + '-deploy'

            # Request new data, it updates automatically
            data.getForceschedulers(fschedulerName).onNew = (forcesched) ->
                $scope.fscheduler = forcesched
                $scope.builderName = project + '-deploy'

                $scope.submit()

                modal = {}
                modal.modal = $uibModal.open
                    templateUrl: 'buildbot_travis/views/deploydialog.html'
                    controller: 'deployDialogController'
                    resolve:
                        modal: -> modal
                        tag: -> $scope.selectedTag
                        project: -> $scope.selectedProject
                        stage: -> $scope.selectedStage
                        forcesched: -> $scope.fscheduler
                        buildername: -> $scope.builderName

        $scope.deployLatest = (commit, project) ->
            $scope.selectedCommit = commit
            $scope.selectedProject = project

            fschedulerName = $scope.selectedProject + '-deploy'

            # Request new data, it updates automatically
            data.getForceschedulers(fschedulerName).onNew = (forcesched) ->
                $scope.fscheduler = forcesched
                $scope.builderName = project + '-deploy'

                $scope.submit()

                modal = {}
                modal.modal = $uibModal.open
                    templateUrl: 'buildbot_travis/views/deploy_latest_dialog.html'
                    controller: 'deployLatestDialogController'
                    size: 'lg'
                    resolve:
                        modal: -> modal
                        commit: -> $scope.selectedCommit
                        project: -> $scope.selectedProject
                        forcesched: -> $scope.fscheduler
                        buildername: -> $scope.builderName





