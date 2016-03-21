============================
Travis CI Compatibility Shim
============================

This is a setup of Buildbot steps, factories and configuration helpers that
give you the best of buildbot and the best of Travis CI:

 * Builder configuration that lives with the source code
 * Private builds
 * SVN and non-github Git support

Basically we provide a compatibility shim in buildbot that allows it to consume
a ``.travis.yml`` file.


Registering a project
=====================

This is still buildbot. Whilst we can move the build definition out of the way,
we still need to register a builder and set up change sources. There is a
travis.yml in the CI codebase::

    projects:
      - name: project1
        repository: https://svn.example.com/svn/customer/project

Additional config
=================
Some additional configs are available in the master.cfg's travis.yml:

* env: default environment variables for your builder VMs
* not_important_files: configuration for not important files (list of fnmatch). Files matching those configs will not generate builds.

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

We only really support python and mandate that you set the ``language`` to
``python``. However right now there is nothing python specific going on: your
install/script steps can do anything needed.

A future improvement will be to select a different VM image according to language

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


Installing dependencies
-----------------------

Your code is built inside a VM and is thrown away after a build. Thus it is
granted passwordless sudo. This is also true of Travis. Tempting as it was to
add a new ``dependencies`` list to ``.travis.yml`` we stay compatible and
suggest you add before_install steps::

    before_install:
      - sudo apt-get update
      - sudo apt-get install -y -q mydependency

The update ensures that the package index is up to date - without it you may
get "package missing" errors. You pass ``-y`` to the install command so that it
doesn't prompt for human input.


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


Whitelisting and blacklisting branches
--------------------------------------

If you want to black list a set of branches::

    branches:
      except:
        - legacy
        - experimental

And if you want to white list a set of branches::

    branches:
      only:
        - trunk
        - /^deploy-.$/

If you specify both then except will be ignored.

Names surrounded by ``/`` are treated as regular expressions. They will be
handled by the python re module and might behave differently to travis, which
uses ruby.

Deployment
----------

A new Deploy section has been added in the left side menu.
A new "deployment environment(s)" parameter has been added in the Projects Settings section.


WebStatus
=========

Previous version of buildbot_travis had a specific UI. Now the buildbot nine UI has
enough features to be usable for buildbot_travis

Configuration UI has been implemented to have a UI for editing the global yaml file.

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

 * 'job' builder does a single build in a clean VM

 * ``setup-steps`` step dynamically appends ShellCommand steps based on
   contents of ``.travis.yml``

 * when job is over VM is thrown away.

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

Other nice to have features and easy to do with buildbot includes:

* select automatically a docker or VM image based on the language.
    easy to do when this lands in buildbot: http://trac.buildbot.net/ticket/3120

Deploying
=========

"example" directory is available for easy to use example.
