
from .base import BaseFactory
from ..steps import TravisSetupSteps


class TravisFactory(BaseFactory):
    def __init__(self, projectname, repository, vcs_type=None, branch=None, username=None, password=None, subrepos=None):
        BaseFactory.__init__(self, projectname, repository, vcs_type=vcs_type, branch=branch, username=username, password=password, subrepos=subrepos)
        self.addStep(TravisSetupSteps())

