try:
    from buildbot_pkg import setup_www_plugin
except ImportError:
    import sys
    print >> sys.stderr, "Please install buildbot_pkg module in order to install that package, or use the pre-build .whl modules available on pypi"
    sys.exit(1)
from setuptools import find_packages

setup_www_plugin(
    name='buildbot_travis',
    description="Adapt buildbot to work a little more like Travis.",
    keywords="buildbot travis ci",
    url="http://github.com/Jc2k/buildbot_travis",
    author="John Carr",
    author_email="john.carr@unrouted.co.uk",
    license="Apache Software License",
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'buildbot.travis': [
            'git+poller = buildbot_travis.vcs.git:GitPoller',
            'svn+poller = buildbot_travis.vcs.svn:SVNPoller',
            'gerrit = buildbot_travis.vcs.gerrit:Gerrit',
            'github = buildbot_travis.vcs.git:Github',
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
        'buildbot-pkg',
        'klein',
        'PyYAML',
    ],
)
