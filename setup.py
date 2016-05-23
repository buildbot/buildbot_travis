try:
    from buildbot_pkg import setup_www_plugin
except ImportError:
    import sys
    print >> sys.stderr, "Please install buildbot_pkg module in order to install that package, or use the pre-build .whl modules available on pypi"
    sys.exit(1)
from setuptools import find_packages

setup_www_plugin(
    name='buildbot_travis',
    description="Travis CI implemented in Buildbot",
    long_description=open("README.rst").read(),
    keywords="buildbot travis ci",
    url="http://github.com/buildbot/buildbot_travis",
    author="Buildbot community",
    author_email="buildbot-devel@lists.sourceforge.net",
    license="MIT",
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'buildbot.travis': [
            'git+poller = buildbot_travis.vcs.git:GitPoller',
            'gerrit = buildbot_travis.vcs.gerrit:Gerrit',
            'github = buildbot_travis.vcs.git:Github',
            # untested 'svn+poller = buildbot_travis.vcs.svn:SVNPoller',
            ],
        'buildbot.www': [
            'buildbot_travis = buildbot_travis:ep'
        ],
        'console_scripts': [
            'bbtravis=buildbot_travis.cmdline:bbtravis',
        ]
    },
    install_requires=[
        'setuptools',
        'buildbot',
        'buildbot-www',
        'buildbot-slave',
        'klein',
        'PyYAML',
    ],
)
