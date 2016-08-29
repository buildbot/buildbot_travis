============================
Travis CI Compatibility Shim
============================

This is a setup of Buildbot steps, factories and configuration helpers that
give you the best of buildbot and the best of Travis CI:

 * Builder configuration that lives with the source code
 * Private builds
 * non-github SCM support (gerrit, gitlab, github, github enterpris)
 * unlimitted build parallelization on your own infra


Basically we provide a compatibility shim in buildbot that allows it to consume a ``.travis.yml`` file.

buildbot_travis does however not support the full .travis.yml format.

|travis-badge|_ |codecov-badge|_


.. |travis-badge| image:: https://travis-ci.org/buildbot/buildbot_travis.svg?branch=master
.. _travis-badge: https://travis-ci.org/buildbot/buildbot_travis
.. |codecov-badge| image:: http://codecov.io/github/buildbot/buildbot_travis/coverage.svg?branch=master
.. _codecov-badge: http://codecov.io/github/buildbot/buildbot_travis?branch=master


Buildbot Nine UI Plugin
=======================

buildbot_travis is configurable via the web UI.

You can edit the project list, environment variables, not_important files, deployment environments, all through the web UI.

high level configuration is either stored in a yaml file or directly in the configured database.

The config file
===============

This is a ``.travis.yml`` for a typical buildout project::

    language: python

    before_install: python bootstrap.py
    install:./bin/buildout
    script: ./bin/test

You can read more about this file format on the travis-ci website::

    http://about.travis-ci.org/docs/user/build-configuration/

But features not also mentioned on this page might not currently be supported.


Supported languages
-------------------

The list of supported language is depending on your build worker configuration.

With the help of docker, you can create as many images as you need worker configuration.


Actually the language parameter of the defacto travis format does not fully leverage the full possibilities of what you can do with buildbot.

You could think of selecting a different docker image according to the version of software you want to check.
This can avoid the time to setup the worker environment at the beginning of your travis.yml (as you would do in travis saas)


Build Steps
-----------

Travis provides 6 hook points for your builds:

 * before_install
 * install
 * after_install
 * before_script
 * script
 * after_script

We really don't care what you run from these hooks as long as exit code 0 means
success and anything else means fail.

You can provide a single command like this::

    install: ./bin/buildout

Or multiple commands like this::

    install:
      - ./configure
      - ./bin/buildout

Each element of the list in the yaml will create a single step, which is named with the first characters of your command line.

If you want to create a custom name, buildbot_travis supports following syntax::

    script:
      - |
          # build
          ./configure
          make
      - |
          # tests
          make tests


Installing dependencies
-----------------------

The docker image that is used is throw away, and will start from clean state for each build.

You can create a docker image with passwordless sudo, as travis does, so that you can use apt-get::

    before_install:
      - sudo apt-get update
      - sudo apt-get install -y -q mydependency

It is however a better practice and more optimized to just provide a prebuilt docker image which contain what you need.


Environments
------------

You might want to perform multiple builds of the same piece of software. Travis
delivers::

    env:
     - FLAVOUR=blue
     - FLAVOUR=green
     - FLAVOUR=red

    install:
      - ./configure -f $FLAVOUR
      - ./bin/buildout

Commits to this code base will cause builds for blue, green and red flavours.
The environment variables can be used like ordinary environment variables
inside the scripts you run from your ``.travis.yml`` and can be used in the
``.travis.yml`` itself.

``env`` is a list of environment variables. You can specify multiple variables
on a single line like this::

    env:
     - PROP1=foo PROP2=bar


Build Matrix
------------

Your options for ``language`` and ``env`` create an implicit build matrix. A
build matrix is a collection of all the possible combinations of the ``env``
options and language versions. You can fine tine this matrix by excluding
certain combinations, or inserting additional ones.

Here is an example of excluding a combination and inserting an additional
build::

      python:
        - 2.6
        - 2.7

      env:
        - FLAVOUR=apple
        - FLAVOUR=orange

      matrix:
        exclude:
          - python: 2.7
            env: FLAVOUR=orange
        include:
          - python: 2.7
            env: FLAVOUR=banana

This will do an additional build of the ``banana`` build but only for python
2.7. And it will turn off the build for the ``orange`` flavour, again only
for python 2.7.


Deployment
----------

A Deploy section is available in the left side menu.
A "deployment environment(s)" parameter is avalable in the Projects Settings section.
TODO: add more description of this feature

How it works
============

The basic behaviour is:

 * Commit is picked up (polling by default, with additional triggers via
   ``/change_hook/poller?poller=pollername`` web hook

 * Build is scheduled on a 'spawner' builder - this is a builder configured to
   use an ordinary slave

 * Checkout occurs - for the purposes of acquiring the ``.travis.yml`` rather
   than for actually performing a build

 * 'spawner' triggers a build on a 'job' builder for each environment in the
   build matrix defined in ``.travis.yml``

 * 'job' builder does a single build in a clean latent buildslave (VM or docker)

 * ``setup-steps`` step dynamically appends ShellCommand steps based on
   contents of ``.travis.yml``

 * when job is over VM orcontainer is thrown away.

 * The 'spawner' build acts as a way of aggregating the build results in a
   single pass/fail status.

 * MailNotifier subclass uses ``.travis.yml`` found in build history so that
   recipients list and whether or not to mail can be adapted accordingly.
   XXX: this needs to be adapted for nine


TODO
====

This special branch is the nine port of buildbot_travis.
Compared to previous version following features are not yet available

* Custom MailNotifier needs to be adapted for nine data api, in order to get the .travis.yml configuration
* mergerequest should be adapted to the new collapseRequest api
* SVN shall be validated (only git has been tested so far)
* metrics facility is not really specific to travis, and should be available in buildbot master directly
* nextBuild feature shall be reimplemented: allowed to avoid running a spawner when no '-job' slave is available

Compared to original Travis format, here is a non-exaustive list of features known not to be supported

* after_success, after_failure. Not implemented, but easy to add.
* deploy. Deployment step would have to happen after all the matrix subbuilds are succeed


Deploying
=========

"example" directory is available for easy to use example.


Deploying in hyper
===================

::

    IP=<yourFIPaddress>
    container=`hyper run -d -e buildbotURL=http://$IP/ -p 0.0.0.0:9989:9989 -p 0.0.0.0:80:8010 tardyp/buildbot_travis:hyper`
    hyper fip attach $IP $container
    echo go to http://$IP/#/bbtravis/config/workers


And configure your hyper keys in the default hyper worker
You should also configure an authentication plugin in order to protect those keys.
