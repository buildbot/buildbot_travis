
from buildbot.process import factory
from buildbot.steps.source import SVN, Git

class BaseFactory(factory.BuildFactory):
    """
    Generic factory that deals with SVN (or Git)
    """

    def __init__(self, repository, vcs_type=None, branch=None, username=None, password=None):
        factory.BuildFactory.__init__(self, [])

        if not repository.endswith("/"):
            repository += "/"

        if not vcs_type:
            if repository.startswith("https://svn."):
                vcs_type = "svn"
            elif repository.startswith("git://github.com/"):
                vcs_type = "git"

        if not branch:
            branch = dict(svn="trunk", git="master")[vcs_type]

        if vcs_type == "svn":
            self.addStep(SVN(
                baseURL=repository,
                defaultBranch=branch,
                username=username,
                password=password,
                ))

        elif vcs_type == "git":
            self.addStep(Git(
                repourl=repository,
                branch=branch,
                ))

