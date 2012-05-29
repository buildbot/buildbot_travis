
from .base import BaseFactory
from ..steps import TravisRunner, TravisSetupSteps


class TravisFactory(BaseFactory):
    def __init__(self, repository, vcs_type=None, branch=None, username=None, password=None):
        BaseFactory.__init__(self, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)
        #for step in ("before_install", "install", "after_install", "before_script", "script", "after_script"):
        #    self.addStep(TravisRunner(
        #        step = step,
        #        ))
        self.addStep(TravisSetupSteps())

