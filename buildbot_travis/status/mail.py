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
# Copyright 2012-2103 Isotoma Limited

from twisted.internet import defer
from buildbot.status import mail
from buildbot.status.results import FAILURE, SUCCESS, WARNINGS, EXCEPTION, Results

from ..factories import TravisSpawnerFactory
from ..travisyml import TravisYml, TravisYmlInvalid


def getConfiguration(build):
    for step in build.getSteps():
        for log in step.getLogs():
            if log.getName() != '.travis.yml':
                continue

            config = TravisYml()
            config.parse(log.getText())
            return config
    raise TravisYmlInvalid("No configuration found in branch")


def defaultMessage(mode, name, build, results, master_status):
    ss_list = build.getSourceStamps()
    prev = build.getPreviousBuild()

    if results == FAILURE:
        if "change" in mode and prev and prev.getResults() != results or \
               "problem" in mode and prev and prev.getResults() != FAILURE:
            summary = "The build is now failing"
            tagline = "failing"
        else:
            summary = "The build is still failing"
            tagline = "still failing"

    elif results == WARNINGS:
        summary = "The build finished with warnings"
        tagline = "warnings"

    elif results == SUCCESS:
        if "change" in mode and prev and prev.getResults() != results:
            summary = "The failing build was fixed"
            tagline = "fixed"
        else:
            summary == "The build was successful"
            tagline = "success"

    elif results == EXCEPTION:
        summary = "The build failed due to a system error"
        tagline = "system error"

    subject = "[%s] %s #%s" % (tagline, name, build.number)


    text = ["Project: %s" % name]
    text.append("Build: #%s" % build.number)
    # text.append("Duration: Probably a long time")
    text.append("Status: %s" % summary)
    text.append('')

    ss = ss_list[0]
    for change in ss.changes:
        text.append("Commit: %s (%s)" % (change.revision, ss.branch))
        text.append("Author: %s" % change.who)
        text.append("Message:")
        for line in change.comments.split("\n"):
            text.append("    " + line)
        text.append("")

    # text.append("View the changeset: %s" % ...)
    # text.append("")

    url = "%s/projects/%s/%s" % (master_status.getBuildbotURL(), name, build.number)
    text.append("View the full build log and details: %s" % url)
    text.append("")

    text.append("--")
    text.append("You can configure recipients for build notifications in your .travis.yml file.")

    return { 'body': '\n'.join(text), 'type': 'plain', 'subject': subject, }


def defaultGetPreviousBuild(current_build):
    iden = set((ss.codebase, ss.branch,) for ss in build.getSourceStamps())

    prev = current_build.getPreviousBuild()
    while prev:
        iden2 = set((ss.codebase, ss.branch,) for ss in build.getSourceStamps())
        if iden == iden2:
            return prev
        prev = current_build.getPreviousBuild()


class MailNotifier(mail.MailNotifier):

    def __init__(self, fromaddr,
            messageFormatter=defaultMessage,
            previousBuildGetter=defaultGetPreviousBuild,
            **kwargs):

        self.getPreviousBuild = previousBuildGetter

        mail.MailNotifier.__init__(self, fromaddr,
            messageFormatter=messageFormatter,
            **kwargs)

    def isMailNeeded(self, build, results):
        builder = build.getBuilder()
        builder_config = filter(lambda b: b.name == builder.name, self.master.config.builders)[0]

        # This notifier will only generate emails for the "spawner" builds
        if not isinstance(builder_config.factory, TravisSpawnerFactory):
            return False

        # That have valid configuration
        try:
            config = getConfiguration(build)
        except TravisYmlInvalid:
            return False

        # And emails are enabled
        if not config.email.enabled:
            return False

        def decide(config):
            if config == "never":
                return False
            elif config == "always":
                return True
            elif config == "change":
                prev = self.getPreviousBuild(build)
                if not prev:
                    return False
                return prev.getResults() != results
            return False

        if results == SUCCESS:
            return decide(config.email.success)
        return decide(config.email.failure)

    def getTravisAddresses(self, build):
        config = getConfiguration(build)
        return config.email.addresses

    @defer.inlineCallbacks
    def useLookup(self, build):
        recipients = self.getTravisAddresses(build)
        if not recipients:
            recipients = yield mail.MailNotifier.useLookup(self, build)
        defer.returnValue(recipients)

    @defer.inlineCallbacks
    def useUsers(self, build):
        recipients = self.getTravisAddresses(build)
        if not recipients:
            recipients = yield mail.MailNotifier.useUsers(self, build)
        defer.returnValue(recipients)
