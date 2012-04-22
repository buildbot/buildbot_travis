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


Example
=======

This is a ``.travis.yml`` for a typical buildout project::

    language: python

    before_install: python bootstrap.py
    install:./bin/buildout
    script: ./bin/test

You can read more about this file format on the travis-ci website::

    http://about.travis-ci.org/docs/user/build-configuration/

But features not also mentioned on this page might not currently be supported.


Registering a project
=====================

This is still buildbot. Whilst we can move the build definition out of the way,
we still need to register a builder and set up SVN polling. There is a
travis.yay in the CI codebase::

    projects:
      - name: project1
        repository: https://svn.example.com/svn/customer/project


Supported languages
===================

We only really support python and mandate that you set the ``language`` to
``python``. However right now there is nothing python specific going on: your
install/script steps can do anything needed.


Build Steps
===========

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
=======================

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
============

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


Whitelisting and blacklisting branches
======================================

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


WebStatus
=========

This repository contains a set of ``HtmlResource`` classes for implementing a
UI that works somewhat like the ``/console`` view.


How it works
============

This is really not something djmitche has in mind when he fires up vim and
starts hacking on buildbot :)

The runner
----------

We can't dynamically change a Factory so instead we have a single step for each
phase (e.g. ``install`` or ``before_script``). Multiple commands can be
executed by that step (by reading them from .travis.yml), but they will be
logged under a single step. Any phases that don't execute commands will be
hidden from the UI.

All build properties are exposed as environment variables in the runner phases.

Triggerable scheduler
---------------------

The main CI job is just calls each of the phases in turn. It is wrapped in a
Triggerable scheduler.

This job will run in a throwaway VM.

Spawner
-------

The CI job that is actually wired up to repository polling.

Commits trigger a spawner build. This is meant to be lightweight so will take
steps to be fast: keeping caches, not being a throw away VM etc.

It's job is to read the ``.travis.yml`` file and see what actions are actually
required. If a source code change doesn't match the branch requirements no
further actions are taken. But if it does, a build will be created for each
environment listed in ``env``.

Build merging
-------------

A custom ``mergeRequests`` handler is provided that considers build properties
from ``.travis.yml`` when decided if builds can be merged.

