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
travis.yay in the CI codebase::

    projects:
      - name: project1
        repository: https://svn.example.com/svn/customer/project


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


WebStatus
=========

This repository contains a set of ``HtmlResource`` classes for implementing a
UI that works somewhat like the ``/console`` view.

The root resource is ``Projects``. It provides a simple list of registered
projects which are colour coded to indicate the state of the build.

.. image:: https://raw.github.com/Jc2k/buildbot_travis/master/docs/images/status.projects.png
   :align: center

When a user drills down in to a particular project they see a ``ProjectStatus``
view. This is basically a list of commits with colour coding to indicate
whether the corresponding build was successful or not.

.. image:: https://raw.github.com/Jc2k/buildbot_travis/master/docs/images/status.commits.png
   :align: center

Drilling down to a particular revision reveals a ``Build`` view. Of particular
interest here is the build matrix which shows a summary of all the builds this
commit triggered. A detail view of each build follows on he same page.

.. image:: https://raw.github.com/Jc2k/buildbot_travis/master/docs/images/status.build.png
   :align: center


How it works
============

This is really not something djmitche has in mind when he fires up vim and
starts hacking on buildbot :)

The basic behaviour is:

 * Commit is picked up (polling by default, with additional triggers via
   ``/change_hook/poller?poller=pollername`` web hook

 * Build is scheduled on a 'spawner' builder - this is a builder configured to
   use an ordinary slave

 * Checkout occurs - for the purposes of acquiring the ``.travis.yml`` rather
   than for actually performing a build

 * 'spawner' triggers a build on a 'job' builder for each environment in the
   build matrix defined in ``.travis.yml``

 * A custom ``mergeRequests`` handler is provided that considers build
   properties from ``.travis.yml`` when decided if builds can be merged.

 * 'job' builder does a single build in a clean VM

 * ``setup-steps`` step dynamically appends ShellCommand steps based on
   contents of ``.travis.yml``

 * when job is over VM is thrown away.

 * The 'spawner' build acts as a way of aggregating the build results in a
   single pass/fail status.

 * MailNotifier subclass uses ``.travis.yml`` found in build history so that
   recipients list and whether or not to mail can be adapted accordingly.


Deploying
=========

Don't. She's not ready.

.. image:: http://alex-holmes.com/b/soon.jpg
   :align: center

