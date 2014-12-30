from setuptools import setup, find_packages

version = '0.0.19.dev0'

setup(
    name='buildbot_travis',
    version=version,
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
            'svn+poller = buildbot_travis.vcs.svn:SVNPoller'
            # TBD
            # 'git+pbhook = buildbot_travis.vcs.git:GitPb',
            # 'git+githubhook = buildbot_travis.vcs.git:Github'
            ]
    },
    install_requires=[
        'setuptools',
        'buildbot',
        'PyYAML',
    ],
)
