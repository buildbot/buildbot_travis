from buildbot.www.plugin import Application
from .api import Api

# create the interface for the setuptools entry point
ep = Application(__package__, "Buildbot travis custom ui")
api = Api(ep)
ep.resource.putChild(b"api", api.app.resource())
