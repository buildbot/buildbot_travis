
from .mergereq import mergeRequests
from .loader import Loader

# We sometimes monkey patch older buildbots to work like newer buildbots
# That's because at present buildbot doesn't try to maintain any API compat at
# all...
from .monkeypatches import patch_all
patch_all()
del patch_all

