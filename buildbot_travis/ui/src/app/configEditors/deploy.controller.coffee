class Deploy
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
        gitTagRevisionMap = []
        gitTagRevisionMapDict = {}
        projectsDict = {}
        data = []

        # We need access to the deliverables names / stages / GIT tags / commit-description property
        @$scope.cfg = angular.copy(config.plugins.buildbot_travis.cfg)

        # Automatically closes all the bindings when the $scope is destroyed
        data = dataService.open().closeOnDestroy($scope)

        # key = The key by which to index the dictionary
        Array::toDict = (key) ->
            @reduce ((dict, obj) -> dict[ obj[key] ] = obj if obj[key]?; return dict), {}

        # Retrieve information on projects where autodeployment is enabled
        filterProjects = ->
            for p in $scope.cfg.projects
                if p.stages? and p.stages.length > 0
                    $scope.projectsFiltered.push(p)

        # Init all the objects that will help for the mapping between BB Travis builds and GIT data (commits, tags)
        initMappingBuildGitData = ->
            for p in $scope.projectsFiltered
                # Object to store the latest versions (GIT tags) deployed in each stage per project
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
                # Object to store the GIT tags per project
                projGitTag = {}
                projGitTag.projectName = p.name
                projGitTag.projectGitTags = ['NA']
                gitTagsByProject.push(projGitTag)
                # Object to store the merged commits per project (ie not yet GIT tagged)
                projVersion = {}
                projVersion.projectName = p.name
                projVersion.versions = []
                $scope.untaggedVersionsByProject.push(projVersion)
                # Object to handle mapping between revision and GIT tag
                tagRev = {}
                tagRev.projectName = p.name
                tagRev.map = []
                pair = {}
                pair.tag = 'NA'
                pair.rev = '0'
                tagRev.map.push(pair)
                gitTagRevisionMap.push(tagRev)


            $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName')
            $scope.gitTagsByProjectDict = gitTagsByProject.toDict('projectName')
            $scope.untaggedVersionsByProjectDict = $scope.untaggedVersionsByProject.toDict('projectName')
            projectsDict = $scope.cfg.projects.toDict('name')
            gitTagRevisionMapDict = gitTagRevisionMap.toDict('name')

        $scope.isStageUndefined = (project, stage)->
            isUndefined = true
            if projectsDict? and projectsDict[project].stages?
                if stage in projectsDict[project].stages
                    isUndefined = false
                return isUndefined
            else
                return isUndefined

        retrieveLatestCommits = (builder) ->
            data.getBuilds(limit: 50, order: '-complete_at', builderid: builder.builderid, complete: 'true', results: 0).onChange = (builds) ->
                for build in builds
                    build.getProperties().onNew = (properties) ->
                        if properties['branch']?
                            # NOT GIT tagged versions - 'post-commit' stages candidates
                            if not properties['branch'][0].match(/tags/)
                                projectName = properties['codebase'][0]
                                if properties['revision']?
                                    for version in $scope.untaggedVersionsByProject
                                        if projectName == version.projectName and properties['revision'][0] not in version.versions
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
                                                for r in gitTagRevisionMap
                                                    if projectName == r.projectName
                                                        new_entry_map = {}
                                                        new_entry_map.tag = properties['commit-description'][0][projectName]
                                                        new_entry_map.rev = properties['got_revision'][0][projectName]
                                                        r.map.push(new_entry_map)
                                                gitTagRevisionMapDict = gitTagRevisionMap.toDict('projectName')
                                    $scope.gitTagsByProjectDict = gitTagsByProject.toDict('projectName')


        retrieveDeployedVersions = (builder) ->
            data.getBuilds(limit: 50, order: '-complete_at', builderid: builder.builderid, complete: 'true', results: 0).onChange = (builds) ->
                for build in builds
                    build.getProperties().onNew = (properties) ->
                        if properties?
                            projectName = properties['codebase'][0]
                            # With a defined version property (ie commit has been GIT tagged)
                            if properties['version'][0]? and properties['version'][0] != ''
                                if properties['stage'][0]? and properties['stage'][0] != ''
                                    if latestDeployedVersionByProject != []
                                        for p in latestDeployedVersionByProject
                                            if p.projectName == projectName
                                                for s in p.stages
                                                    if s.stage == properties['stage'][0] and s.versions[0] == 'NA'
                                                        s.versions = []
                                                        s.versions.push(properties['version'][0])
                                                    else
                                                        new_version = properties['version'][0]
                                                        if new_version not in s.versions
                                                            s.versions.push(new_version)
                                                stage_info = {}
                                                stage_info = p.stages.toDict('stage')
                                                p.stages_sorted = stage_info
                                        $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName')
                            # Without a defined version property (ie commit has not been GIT tagged yet, GIT tag is generated by the deploy build)
                            else if properties['revision'][0]? and properties['revision'][0] != '' and properties['version'][0] == ''
                                if properties['stage'][0]? and properties['stage'][0] != ''
                                    if latestDeployedVersionByProject != []
                                        for p in latestDeployedVersionByProject
                                            if p.projectName == projectName and gitTagRevisionMapDict[projectName]?
                                                for x in gitTagRevisionMapDict[projectName].map
                                                    if x.rev == properties['revision'][0]
                                                        for s in p.stages
                                                            if s.stage == properties['stage'][0] and s.versions[0] == 'NA'
                                                                s.versions = []
                                                                s.versions.push(x.tag)
                                                            else
                                                                new_version = x.tag
                                                                if new_version not in s.versions
                                                                    s.versions.push(new_version)
                                                        stage_info = {}
                                                        stage_info = p.stages.toDict('stage')
                                                        p.stages_sorted = stage_info
                                        $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName')

        retrieveInfo = ->
            # Retrieve the commit-description properties that contain ALL the versions (tagged or not)
            # First case : dev have been successfully merged, ready to be deployed in 'post commit' stages - not GIT tagged yet
            # Second case : dev have been deployed in 'post commit' stages - GIT tagged
            data.getBuilders().onNew = (builder) ->
                name = ''
                name = builder.name

                for p, k in $scope.projectsFiltered
                    if name.match(p.name)
                        if not name.match(/-deploy/) and not name.match(/-job/) and not name.match(/-try/)
                            retrieveLatestCommits(builder)

                        else if name.match(/-deploy/)
                            retrieveDeployedVersions(builder)

                        else
                            return

        filterProjects()
        initMappingBuildGitData()
        retrieveInfo()

        $scope.deploy = (tag, project, stage) ->
            $scope.selectedTag = tag
            $scope.selectedProject = project
            $scope.selectedStage = stage

            fschedulerName = $scope.selectedProject + '-deploy'

            # Request new data, it updates automatically
            data.getForceschedulers(fschedulerName).onNew = (forcesched) ->
                $scope.fscheduler = forcesched
                $scope.builderName = project + '-deploy'

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







angular.module('app')
.controller('deployController', ['$scope', '$state', '$uibModal', 'config', 'dataService', Deploy])