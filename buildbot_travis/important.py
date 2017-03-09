from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import fnmatch
import re


class ImportantManager(object):

    def __init__(self, globlist):
        if globlist:
            self.globlist_re = re.compile(
                "(" + "|".join([fnmatch.translate(g) for g in globlist]) + ")"
            )
        else:
            self.globlist_re = None

    def fileIsImportant(self, change):
        # Ignore "branch created"
        if len(change.files) == 1 and change.files[0] == '':
            return False

        if self.globlist_re is None:
            return True
        for f in change.files:
            dirname = ''
            if "/" in f:
                dirname, f = f.rsplit("/", 1)
            if self.globlist_re.match(f):
                continue

            return True

        return False
