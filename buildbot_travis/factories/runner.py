class TravisFactory(CiFactory):
    
    def __init__(self, repository, vcs_type=None, branch=None, username=None, password=None):
        CiFactory.__init__(self, repository, vcs_type=vcs_type, branch=branch, username=username, password=password)
        
        self.addStep(FileDownload(
                                  mastersrc=sibpath("travis-runner.py"),
                                  slavedest="travis-runner",
                                  mode=0755,
                                  ))
        
        self.addStep(ShellCommand(
                                  name="apt-get-update",
                                  description="apt-get-update",
                                  flunkOnFailure=True,
                                  haltOnFailure=True,
                                  command="sudo apt-get update",
                                  ))
        
        self.addStep(ShellCommand(
                                  name="apt-get-deps",
                                  description="apt-get-deps",
                                  flunkOnFailure=True,
                                  haltOnFailure=True,
                                  command="sudo apt-get install -y -q python-yaml",
                                  ))
        
        for step in ("before-install", "install", "after-install", "before-script", "script", "after-script"):
            self.addStep(TravisRunner(
                                      step = step,
                                      ))