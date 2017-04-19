from __future__ import absolute_import, division, print_function

from setuptools import find_packages

try:
    from buildbot_pkg import setup_www_plugin
except ImportError:
    import sys
    print("Please install buildbot_pkg module in order to install that package, or use the pre-build .whl modules available on pypi", file=sys.stderr)
    sys.exit(1)

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
            'github = buildbot_travis.vcs.github:GitHub',
            'gitpb = buildbot_travis.vcs.git:GitPb',
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
        'buildbot>=0.9.6',  # for virtual builders features
        'buildbot-www',
        'buildbot-console-view',
        'buildbot-waterfall-view',
        'buildbot-worker',
        'klein',
        'urwid',
        'PyYAML',
        'txrequests',
        'pyjade',
        'txgithub',
        'ldap3',
        'hyper_sh',
        'future'
    ],
)
