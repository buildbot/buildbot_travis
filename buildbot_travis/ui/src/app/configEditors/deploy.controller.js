// decaffeinate runs into this bug with this file: https://github.com/decaffeinate/decaffeinate/issues/1480
(function() {
  let Deploy,
      {
        indexOf
      } = [];

  Deploy = (function() {
    let self;

    class Deploy {
      constructor($scope, $state, $uibModal, config, dataService) {
        let data, filterProjects, gitTagRevisionMap, gitTagRevisionMapDict, gitTagsByProject, initMappingBuildGitData, latestDeployedVersionByProject, projectsDict, retrieveDeployedVersions, retrieveInfo, retrieveLatestCommits;
        self = this;
        self.$scope = $scope;
        $scope.title = 'Deployment info';
        $scope.fscheduler = '';
        $scope.builderName = '';
        $scope.latestDeployedVersionByProjectDict = {};
        $scope.gitTagsByProjectDict = {};
        $scope.untaggedVersionsByProject = [];
        $scope.untaggedVersionsByProjectDict = {};
        $scope.projectsFiltered = [];
        latestDeployedVersionByProject = [];
        gitTagsByProject = [];
        gitTagRevisionMap = [];
        gitTagRevisionMapDict = {};
        projectsDict = {};
        data = [];
        // We need access to the deliverables names / stages / GIT tags / commit-description property
        this.$scope.cfg = angular.copy(config.plugins.buildbot_travis.cfg);
        // Automatically closes all the bindings when the $scope is destroyed
        data = dataService.open().closeOnDestroy($scope);
        // key = The key by which to index the dictionary
        Array.prototype.toDict = function(key) {
          return this.reduce((function(dict, obj) {
            if (obj[key] != null) {
              dict[obj[key]] = obj;
            }
            return dict;
          }), {});
        };
        // Retrieve information on projects where autodeployment is enabled
        filterProjects = function() {
          let i, len, p, ref, results;
          ref = $scope.cfg.projects;
          results = [];
          for (i = 0, len = ref.length; i < len; i++) {
            p = ref[i];
            if ((p.stages != null) && p.stages.length > 0) {
              results.push($scope.projectsFiltered.push(p));
            } else {
              results.push(void 0);
            }
          }
          return results;
        };
        // Init all the objects that will help for the mapping between BB Travis builds and GIT data (commits, tags)
        initMappingBuildGitData = function() {
          let depInfo, i, j, latestDeployedVersion, len, len1, p, pair, projGitTag, projVersion, ref, ref1, s, tagRev;
          ref = $scope.projectsFiltered;
          for (i = 0, len = ref.length; i < len; i++) {
            p = ref[i];
            // Object to store the latest versions (GIT tags) deployed in each stage per project
            latestDeployedVersion = {};
            latestDeployedVersion.projectName = p.name;
            latestDeployedVersion.stages_sorted = {};
            latestDeployedVersion.stages = [];
            ref1 = p.stages;
            for (j = 0, len1 = ref1.length; j < len1; j++) {
              s = ref1[j];
              depInfo = {};
              depInfo.stage = '';
              depInfo.versions = [];
              depInfo.versions = ['NA'];
              depInfo.stage = s;
              latestDeployedVersion.stages.push(depInfo);
            }
            latestDeployedVersionByProject.push(latestDeployedVersion);
            // Object to store the GIT tags per project
            projGitTag = {};
            projGitTag.projectName = p.name;
            projGitTag.projectGitTags = ['NA'];
            gitTagsByProject.push(projGitTag);
            // Object to store the merged commits per project (ie not yet GIT tagged)
            projVersion = {};
            projVersion.projectName = p.name;
            projVersion.versions = [];
            $scope.untaggedVersionsByProject.push(projVersion);
            // Object to handle mapping between revision and GIT tag
            tagRev = {};
            tagRev.projectName = p.name;
            tagRev.map = [];
            pair = {};
            pair.tag = 'NA';
            pair.rev = '0';
            tagRev.map.push(pair);
            gitTagRevisionMap.push(tagRev);
          }
          $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName');
          $scope.gitTagsByProjectDict = gitTagsByProject.toDict('projectName');
          $scope.untaggedVersionsByProjectDict = $scope.untaggedVersionsByProject.toDict('projectName');
          projectsDict = $scope.cfg.projects.toDict('name');
          return gitTagRevisionMapDict = gitTagRevisionMap.toDict('name');
        };
        $scope.isStageUndefined = function(project, stage) {
          let isUndefined;
          isUndefined = true;
          if ((projectsDict != null) && (projectsDict[project].stages != null)) {
            if (indexOf.call(projectsDict[project].stages, stage) >= 0) {
              isUndefined = false;
            }
            return isUndefined;
          } else {
            return isUndefined;
          }
        };
        retrieveLatestCommits = builder => data.getBuilds({
          limit: 50,
          order: '-complete_at',
          builderid: builder.builderid,
          complete: 'true',
          results: 0
        }).onChange = function(builds) {
          let build, i, len, results;
          results = [];
          for (i = 0, len = builds.length; i < len; i++) {
            build = builds[i];
            results.push(build.getProperties().onNew = function(properties) {
              let g, j, l, len1, len2, len3, m, new_entry_map, new_version, projectName, r, ref, ref1, ref2, ref3, version;
              if (properties['branch'] != null) {
                // NOT GIT tagged versions - 'post-commit' stages candidates
                if (!properties['branch'][0].match(/tags/)) {
                  projectName = properties['codebase'][0];
                  if (properties['revision'] != null) {
                    ref = $scope.untaggedVersionsByProject;
                    for (j = 0, len1 = ref.length; j < len1; j++) {
                      version = ref[j];
                      if (projectName === version.projectName && (ref1 = properties['revision'][0], indexOf.call(version.versions, ref1) < 0)) {
                        new_version = properties['revision'][0];
                        version.versions.push(new_version);
                      }
                    }
                    $scope.untaggedVersionsByProjectDict = $scope.untaggedVersionsByProject.toDict('projectName');
                  }
                }
                // GIT tagged versions
                if (properties['branch'][0].match(/tags/)) {
                  projectName = properties['codebase'][0];
                  if (properties['commit-description'] != null) {
                    for (l = 0, len2 = gitTagsByProject.length; l < len2; l++) {
                      g = gitTagsByProject[l];
                      if (projectName === g.projectName) {
                        if (ref2 = properties['commit-description'][0], indexOf.call(g.projectGitTags, ref2) < 0) {
                          new_version = [];
                          new_version = properties['commit-description'][0];
                          if (g.projectGitTags[0] === 'NA') {
                            g.projectGitTags = [];
                          }
                          if (ref3 = new_version[projectName], indexOf.call(g.projectGitTags, ref3) < 0) {
                            g.projectGitTags.push(new_version[projectName]);
                          }
                          for (m = 0, len3 = gitTagRevisionMap.length; m < len3; m++) {
                            r = gitTagRevisionMap[m];
                            if (projectName === r.projectName) {
                              new_entry_map = {};
                              new_entry_map.tag = properties['commit-description'][0][projectName];
                              new_entry_map.rev = properties['got_revision'][0][projectName];
                              r.map.push(new_entry_map);
                            }
                          }
                          gitTagRevisionMapDict = gitTagRevisionMap.toDict('projectName');
                        }
                      }
                    }
                    return $scope.gitTagsByProjectDict = gitTagsByProject.toDict('projectName');
                  }
                }
              }
            });
          }
          return results;
        };
        retrieveDeployedVersions = builder => data.getBuilds({
          limit: 50,
          order: '-complete_at',
          builderid: builder.builderid,
          complete: 'true',
          results: 0
        }).onChange = function(builds) {
          let build, i, len, results;
          results = [];
          for (i = 0, len = builds.length; i < len; i++) {
            build = builds[i];
            results.push(build.getProperties().onNew = function(properties) {
              let j, l, len1, len2, len3, len4, len5, m, n, new_version, o, p, projectName, ref, ref1, ref2, s, stage_info, x;
              if (properties != null) {
                projectName = properties['codebase'][0];
                // With a defined version property (ie commit has been GIT tagged)
                if ((properties['version'][0] != null) && properties['version'][0] !== '') {
                  if ((properties['stage'][0] != null) && properties['stage'][0] !== '') {
                    if (latestDeployedVersionByProject !== []) {
                      for (j = 0, len1 = latestDeployedVersionByProject.length; j < len1; j++) {
                        p = latestDeployedVersionByProject[j];
                        if (p.projectName === projectName) {
                          ref = p.stages;
                          for (l = 0, len2 = ref.length; l < len2; l++) {
                            s = ref[l];
                            if (s.stage === properties['stage'][0] && s.versions[0] === 'NA') {
                              s.versions = [];
                              s.versions.push(properties['version'][0]);
                            } else {
                              new_version = properties['version'][0];
                              if (indexOf.call(s.versions, new_version) < 0) {
                                s.versions.push(new_version);
                              }
                            }
                          }
                          stage_info = {};
                          stage_info = p.stages.toDict('stage');
                          p.stages_sorted = stage_info;
                        }
                      }
                      return $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName');
                    }
                  }
                // Without a defined version property (ie commit has not been GIT tagged yet, GIT tag is generated by the deploy build)
                } else if ((properties['revision'][0] != null) && properties['revision'][0] !== '' && properties['version'][0] === '') {
                  if ((properties['stage'][0] != null) && properties['stage'][0] !== '') {
                    if (latestDeployedVersionByProject !== []) {
                      for (m = 0, len3 = latestDeployedVersionByProject.length; m < len3; m++) {
                        p = latestDeployedVersionByProject[m];
                        if (p.projectName === projectName && (gitTagRevisionMapDict[projectName] != null)) {
                          ref1 = gitTagRevisionMapDict[projectName].map;
                          for (n = 0, len4 = ref1.length; n < len4; n++) {
                            x = ref1[n];
                            if (x.rev === properties['revision'][0]) {
                              ref2 = p.stages;
                              for (o = 0, len5 = ref2.length; o < len5; o++) {
                                s = ref2[o];
                                if (s.stage === properties['stage'][0] && s.versions[0] === 'NA') {
                                  s.versions = [];
                                  s.versions.push(x.tag);
                                } else {
                                  new_version = x.tag;
                                  if (indexOf.call(s.versions, new_version) < 0) {
                                    s.versions.push(new_version);
                                  }
                                }
                              }
                              stage_info = {};
                              stage_info = p.stages.toDict('stage');
                              p.stages_sorted = stage_info;
                            }
                          }
                        }
                      }
                      return $scope.latestDeployedVersionByProjectDict = latestDeployedVersionByProject.toDict('projectName');
                    }
                  }
                }
              }
            });
          }
          return results;
        };
        retrieveInfo = () => // Retrieve the commit-description properties that contain ALL the versions (tagged or not)
        // First case : dev have been successfully merged, ready to be deployed in 'post commit' stages - not GIT tagged yet
        // Second case : dev have been deployed in 'post commit' stages - GIT tagged
        data.getBuilders().onNew = function(builder) {
          let i, k, len, name, p, ref;
          name = '';
          ({
            name
          } = builder);
          ref = $scope.projectsFiltered;
          for (k = i = 0, len = ref.length; i < len; k = ++i) {
            p = ref[k];
            if (name.match(p.name)) {
              if (!name.match(/-deploy/) && !name.match(/-job/) && !name.match(/-try/)) {
                retrieveLatestCommits(builder);
              } else if (name.match(/-deploy/)) {
                retrieveDeployedVersions(builder);
              } else {
                return;
              }
            }
          }
        };
        filterProjects();
        initMappingBuildGitData();
        retrieveInfo();
        $scope.deploy = function(tag, project, stage) {
          let fschedulerName;
          $scope.selectedTag = tag;
          $scope.selectedProject = project;
          $scope.selectedStage = stage;
          fschedulerName = $scope.selectedProject + '-deploy';
          // Request new data, it updates automatically
          return data.getForceschedulers(fschedulerName).onNew = function(forcesched) {
            let modal;
            $scope.fscheduler = forcesched;
            $scope.builderName = project + '-deploy';
            modal = {};
            return modal.modal = $uibModal.open({
              templateUrl: 'buildbot_travis/views/deploydialog.html',
              controller: 'deployDialogController',
              resolve: {
                modal() {
                  return modal;
                },

                tag() {
                  return $scope.selectedTag;
                },

                project() {
                  return $scope.selectedProject;
                },

                stage() {
                  return $scope.selectedStage;
                },

                forcesched() {
                  return $scope.fscheduler;
                },

                buildername() {
                  return $scope.builderName;
                }
              }
            });
          };
        };
        $scope.deployLatest = function(commit, project) {
          let fschedulerName;
          $scope.selectedCommit = commit;
          $scope.selectedProject = project;
          fschedulerName = $scope.selectedProject + '-deploy';
          // Request new data, it updates automatically
          return data.getForceschedulers(fschedulerName).onNew = function(forcesched) {
            let modal;
            $scope.fscheduler = forcesched;
            $scope.builderName = project + '-deploy';
            modal = {};
            return modal.modal = $uibModal.open({
              templateUrl: 'buildbot_travis/views/deploy_latest_dialog.html',
              controller: 'deployLatestDialogController',
              size: 'lg',
              resolve: {
                modal() {
                  return modal;
                },

                commit() {
                  return $scope.selectedCommit;
                },

                project() {
                  return $scope.selectedProject;
                },

                forcesched() {
                  return $scope.fscheduler;
                },

                buildername() {
                  return $scope.builderName;
                }
              }
            });
          };
        };
      }

    };

    self = null;

    return Deploy;

  }).call(this);

  angular.module('app').controller('deployController', ['$scope', '$state', '$uibModal', 'config', 'dataService', Deploy]);

}).call(this);
