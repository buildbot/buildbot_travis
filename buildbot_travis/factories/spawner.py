
from .base import BaseFactory
from ..steps import TravisTrigger


class TravisSpawnerFactory(BaseFactory):

    def __init__(self, projectname, scheduler, repository, vcs_type=None, branch=None, username=None, password=None):
        BaseFactory.__init__(self, projectname, repository, vcs_type=vcs_type,
                             branch=branch, username=username, password=password)

        self.addStep(TravisTrigger(
            scheduler=scheduler,
        ))
