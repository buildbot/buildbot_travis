
import inspect


def patch_process_build_Build_getSourceStamp():
    from buildbot.process.build import Build
    args, varargs, keywords, defaults = inspect.getargspec(Build.getSourceStamp)
    if not "codebase" in args:
        old_getSourceStamp = Build.getSourceStamp
        def getSourceStamp(self, codebase=''):
            return old_getSourceStamp(self)
        Build.getSourceStamp = getSourceStamp

def patch_all():
    patch_process_build_Build_getSourceStamp()

