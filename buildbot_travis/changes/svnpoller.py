# Copyright 2012-2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from buildbot.changes import svnpoller
from twisted.python import log


class SVNFile:
    repository = None
    project = None
    branch = None
    path = None


class SVNPoller(svnpoller.SVNPoller):

    def _transform_path(self, path):
        where = svnpoller.SVNPoller._transform_path(self, path)
        if isinstance(where, tuple):
            f = SVNFile()
            f.branch, f.path = where
            return f
        return where

    def create_changes(self, new_logentries):
        changes = []

        for el in new_logentries:
            revision = str(el.getAttribute("revision"))

            revlink = ''

            if self.revlinktmpl:
                if revision:
                    revlink = self.revlinktmpl % urllib.quote_plus(revision)

            log.msg("Adding change revision %s" % (revision,))
            author = self._get_text(el, "author")
            comments = self._get_text(el, "msg")
            # there is a "date" field, but it provides localtime in the
            # repository's timezone, whereas we care about buildmaster's
            # localtime (since this will get used to position the boxes on
            # the Waterfall display, etc). So ignore the date field, and
            # addChange will fill in with the current time
            branches = {}
            try:
                pathlist = el.getElementsByTagName("paths")[0]
            except IndexError:  # weird, we got an empty revision
                log.msg("ignoring commit with no paths")
                continue

            for p in pathlist.getElementsByTagName("path"):
                action = p.getAttribute("action")
                path = "".join([t.data for t in p.childNodes])
                # the rest of buildbot is certaily not yet ready to handle
                # unicode filenames, because they get put in RemoteCommands
                # which get sent via PB to the worker, and PB doesn't
                # handle unicode.
                path = path.encode("ascii")
                if path.startswith("/"):
                    path = path[1:]
                where = self._transform_path(path)

                # if 'where' is None, the file was outside any project that
                # we care about and we should ignore it
                if where:
                    key = (where.project, where.repository, where.branch)
                    if key in branches:
                        branches[key] = {'files': []}
                    branches[key]['files'].append(where.path)

                    if not branches[key].has_key('action'):
                        branches[key]['action'] = action

            for key in branches.keys():
                project, repository, branch = key
                action = branches[key]['action']
                files = branches[key]['files']
                number_of_files_changed = len(files)

                if action == u'D' and number_of_files_changed == 1 and files[0] == '':
                    log.msg("Ignoring deletion of branch '%s'" % branch)
                else:
                    chdict = dict(
                        author=author,
                        files=files,
                        comments=comments,
                        revision=revision,
                        branch=branch,
                        revlink=revlink,
                        category=self.category,
                        repository=repository or self.svnurl,
                        project=project or self.project)
                    changes.append(chdict)

        return changes
