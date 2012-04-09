
class TravisFactory(CiFactory):
    
    def __init__(self, repository, vcs_type=None, branch=None, username=None, password=None):
        CiFactory.__init__(self, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)
        
        for step in ("before-install", "install", "after-install", "before-script", "script", "after-script"):
            self.addStep(TravisRunner(
                step = step,
                ))

