from setuptools import setup, find_packages

version = '0.0.2dev'

setup(
    name = 'buildbot_travis',
    version = version,
    description = "Adapt buildbot to work a little more like Travis.",
    keywords = "buildbot travis ci",
    author = "John Carr",
    author_email = "john.carr@unrouted.co.uk",
    license="Apache Software License",
    packages = find_packages(exclude=['ez_setup']),
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'buildbot',
        'PyYAML',
    ],
)
