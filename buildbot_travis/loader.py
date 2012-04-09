from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable

from buildbot_travis.factories import TravisFactory, TravisSpawnerFactory


class Loader(object):

    def __init__(self, config):
        self.config = config

    def define_travis_builder(self):
        f = TravisFactory(
            repository=repository,
            username=username,
            password=password,
            )

        builder = BuilderConfig(
            name = name,
            slavenames = integration_slaves.any(),
            factory = f,
            properties = {
                "base-image": "lucid_base_image",
                "classification": "ci",
                },
             )

        c['builders'].append(builder)

        c['schedulers'].append(Triggerable(name, [name]))

        f = TravisSpawnerFactory(
            repository = repository,
            scheduler = name,
            username = username,
            password = password,
            )

        builder = BuilderConfig(
            name = "%s-spawner" % name,
            slavenames = integration_slaves.any(),
            factory = f,
            category = "spawner",
            )

        c['builders'].append(builder)

        from isotoma.buildbot.utils import get_scheduler
        c['schedulers'].append(get_scheduler(builder, ''))

