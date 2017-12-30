# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from __future__ import absolute_import, division, print_function

import os
import shutil
import tempfile

from twisted.internet import defer

from buildbot.worker import Worker

try:
    from buildbot.test.util.integration import RunMasterBase
except ImportError:
    # if buildbot installed with wheel, it does not include the test util :-(
    RunMasterBase = object


# This integration test creates a master and slave environment,
# with one builder and a custom step
# It uses a git bundle to store sample git repository for the integration test
# inside the git is present the following '.travis.yml' file
# to edit it:
"""
mkdir test.git
cd test.git
git init
git reset --hard `git bundle unbundle ../test.git.bundle |awk '{print $1}'`
vi .travis.yml
git commit -a --am
git bundle create ../test.git.bundle master
"""

travis_yml = """
language: python

label_mapping:
  TWISTED: tw
  SQLALCHEMY: sqla
  SQLALCHEMY_MIGRATE: sqlam
  latest: l
  python: py

python:
  - "2.7"
env:
  global:
      - CI=true
  matrix:
      - TWISTED=11.1.0 SQLALCHEMY=latest SQLALCHEMY_MIGRATE=0.7.1
      - TWISTED=latest SQLALCHEMY=latest SQLALCHEMY_MIGRATE=latest
matrix:
  include:
    # Test different versions of SQLAlchemy
    - python: "2.7"
      env: TWISTED=12.0.0 SQLALCHEMY=0.6.0 SQLALCHEMY_MIGRATE=0.7.1
    - python: "2.7"
      env: TWISTED=12.0.0 SQLALCHEMY=0.6.8 SQLALCHEMY_MIGRATE=0.7.1

before_install:
  - echo doing before install
  - echo doing before install 2nd command
install:
  - echo doing install
script:
  - echo doing scripts
after_success:
  - echo doing after success
notifications:
  email: false
"""


class TravisMaster(RunMasterBase):
    timeout = 300

    def mktemp(self):
        # twisted mktemp will create a very long directory, which virtualenv will not like.
        # https://github.com/pypa/virtualenv/issues/596
        # so we put it in the /tmp directory to be safe
        tmp = tempfile.mkdtemp(prefix="travis_trial")
        self.addCleanup(shutil.rmtree, tmp)
        return os.path.join(tmp, "work")

    @defer.inlineCallbacks
    def test_travis(self):
        yield self.setupConfig(masterConfig())
        change = dict(branch="master",
                      files=["foo.c"],
                      author="me@foo.com",
                      comments="good stuff",
                      revision="HEAD",
                      repository=path_to_git_bundle,
                      project="buildbot_travis"
                      )
        build = yield self.doForceBuild(wantSteps=True, useChange=change, wantLogs=True)
        self.assertEqual(build['steps'][0]['state_string'], 'update buildbot_travis')
        self.assertEqual(build['steps'][0]['name'], 'git-buildbot_travis')
        self.assertEqual(build['steps'][1]['state_string'], 'triggered ' +
                         ", ".join(["buildbot_travis-job"] * 4))
        url_names = [url['name'] for url in build['steps'][1]['urls']]
        url_urls = [url['url'] for url in build['steps'][1]['urls']]
        self.assertIn(u'http://localhost:8010/#builders/3/builds/1', url_urls)
        self.assertIn(u'success: buildbot_travis py:2.7 sqla:l sqlam:l tw:l #1', url_names)
        self.assertEqual(build['steps'][1]['logs'][0]['contents']['content'], travis_yml)

        builds = yield self.master.data.get(("builds",))
        self.assertEqual(len(builds), 5)
        props = {}
        buildernames = {}
        labels = {}
        for build in builds:
            build['properties'] = yield self.master.data.get(("builds", build['buildid'], 'properties'))
            props[build['buildid']] = {
                k: v[0]
                for k, v in build['properties'].items()
                if v[1] == '.travis.yml'
            }
            buildernames[build['buildid']] = build['properties'].get('virtual_builder_name')
            labels[build['buildid']] = build['properties'].get('matrix_label')
        self.assertEqual(props, {
            1: {},
            2: {u'SQLALCHEMY': u'latest',
                u'SQLALCHEMY_MIGRATE': u'0.7.1',
                u'TWISTED': u'11.1.0',
                u'CI': u'true',
                u'python': u'2.7'},
            3: {u'SQLALCHEMY': u'latest',
                u'SQLALCHEMY_MIGRATE': u'latest',
                u'TWISTED': u'latest',
                u'CI': u'true',
                u'python': u'2.7'},
            4: {u'SQLALCHEMY': u'0.6.0',
                u'SQLALCHEMY_MIGRATE': u'0.7.1',
                u'TWISTED': u'12.0.0',
                u'CI': u'true',
                u'python': u'2.7'},
            5: {u'SQLALCHEMY': u'0.6.8',
                u'SQLALCHEMY_MIGRATE': u'0.7.1',
                u'TWISTED': u'12.0.0',
                u'CI': u'true',
                u'python': u'2.7'}})
        # global env CI should not be there
        self.assertEqual(buildernames, {
            1: None,
            2: (u'buildbot_travis py:2.7 sqla:l sqlam:0.7.1 tw:11.1.0', u'spawner'),
            3: (u'buildbot_travis py:2.7 sqla:l sqlam:l tw:l', u'spawner'),
            4: (u'buildbot_travis py:2.7 sqla:0.6.0 sqlam:0.7.1 tw:12.0.0', u'spawner'),
            5: (u'buildbot_travis py:2.7 sqla:0.6.8 sqlam:0.7.1 tw:12.0.0', u'spawner')})
        self.assertEqual(labels, {
            1: None,
            2: (u'py:2.7/sqla:l/sqlam:0.7.1/tw:11.1.0', u'spawner'),
            3: (u'py:2.7/sqla:l/sqlam:l/tw:l', u'spawner'),
            4: (u'py:2.7/sqla:0.6.0/sqlam:0.7.1/tw:12.0.0', u'spawner'),
            5: (u'py:2.7/sqla:0.6.8/sqlam:0.7.1/tw:12.0.0', u'spawner')})


# master configuration
sample_yml = """
projects:
  - name: buildbot_travis
    repository: %(path_to_git_bundle)s
    vcs_type: git+poller
"""

path_to_git_bundle = None


def masterConfig():
    global path_to_git_bundle
    from buildbot_travis import TravisConfigurator
    path_to_git_bundle = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.git.bundle"))
    with open("sample.yml", "w") as f:
        f.write(sample_yml % dict(path_to_git_bundle=path_to_git_bundle))
    c = {}
    c['workers'] = [Worker("local1", "p")]
    TravisConfigurator(c, os.getcwd()).fromYaml("sample.yml")
    return c
