
class TravisSpawnerFactory(CiFactory):
    
    def __init__(self, scheduler, repository, vcs_type=None, branch=None, username=None, password=None):
        CiFactory.__init__(self, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)
        
        self.addStep(TravisTrigger(
                                   scheduler=scheduler,
                                   ))
