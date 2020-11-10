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


QuickStart
==========

First you need to make sure you have the proper python 2.7 environment. On ubuntu 16.04, that would mean::

    sudo apt-get install build-essential python-dev libffi-dev libssl-dev python-pip
    pip install virtualenv

Then you create a virtualenv and install buildbot_travis via pip::

    mkdir bbtravis
    cd bbtravis
    virtualenv sandbox
    . ./sandbox/bin/activate
    pip install buildbot_travis

Now you can create a new master::

    bbtravis create-master master

Now you can start that new master::

    buildbot start master

And then go to the UI: http://localhost:8010  which has an administration panel where to configure the projects.


QuickStart With Docker
======================

::

    docker run -p 8010:8010 -p 9989:9989 buildbot/buildbot-travis


QuickStart With Hyper
=====================

::

    IP=<yourFIPaddress>
    container=`hyper run -d -e buildbotURL=http://$IP/ -p 9989:9989 -p 80:8010 buildbot/buildbot-travis`
    hyper fip attach $IP $container
    echo go to http://$IP/#/bbtravis/config/auth  to configure admin access
    echo go to http://$IP/#/bbtravis/config/workers to configure


Buildbot Nine UI Plugin
=======================

buildbot_travis is configurable via the web UI.

You can edit the project list, environment variables, not_important files, deployment environments, all through the web UI.

high level configuration is either stored in a yaml file or directly in the configured database.

The per project config file
===========================

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


Buildbot specific features
--------------------------

Steps as dictionary
~~~~~~~~~~~~~~~~~~~

Original Travis just create a simple shell script to run the whole CI script.
Buildbot is a little bit more powerful, and buildbot_travis can make use of it.
For this you need to go out of the travis "de-facto" standard. e.g::

    script:
      - |
          # build
          ./configure
          make

      - title: tests
        shell: dash
        condition: TESTS=='tests'
        cmd: make tests

If yaml parser encounters a dictionary, then it will use the following keys:


* ``title``: the title of the step in the UI

* ``shell``: run the cmd inside the given shell.  This is normally not
  necessary, since the buildbot worker will apply the appropriate
  shell (``cmd`` for Windows, ``/bin/sh`` for everything else).  If the
  value is a list, it will be used as is.  Otherwise, it is assumed
  that it uses the option ``-c`` to take a command string.

* ``condition``: a condition to run the step.
   It is evaluated as a python expression, with variables beiing the environment variable generated by your matrix.
   The condition is evaluated at the time of the parsing of the yaml file.
   If the condition is not met, then the step is just not inserted in the step list.

* ``cmd``: The command to run.

* ``step``: The buildbot step create.
    See below for detailled description.
    if defined, ``shell``, ``title`` and ``cmd`` keys are ignored.

.bbtravis.yml
~~~~~~~~~~~~~


In order to keep working with buildbot_travis and travis.org at the same time, buildbot travis will look for a .bbtravis.yml before .travis.yml.
With this, you can keep your .travis.yml without any buildbot specific feature.

Shallow Clone
~~~~~~~~~~~~~

* Original travis supports clone depth configuration inside the yml file (aka shallow clone).
  As the git clone is made before buildbot has a chance to parse the yaml, this configuration is done in the per project config in buildbot travis.
  Two options are available in the cfg.yml (shallow and retryFetch) e.g::

    projects:
    -   branches:
        - master
        name: buildbot
        repository: https://github.com/buildbot/buildbot
        shallow: 200
        mode: "full"
        method: "clobber"
        stages: []
        tags: []
        vcs_type: github

Interpolate
~~~~~~~~~~~

Buildbot has a very useful `Interpolate <http://docs.buildbot.net/latest/manual/cfg-properties.html#interpolate>`_ utility.
If you prepend your scripts by ```!i`` or ``!interpolate``, then buildbot_travis will automatically create an Interpolate object::

      - title: make dist
        cmd: !i make REVISION=%(prop:got_revision:-%(src::revision:-unknown)s)s dist

Commands without shell
~~~~~~~~~~~~~~~~~~~~~~

If cmd is a list, it will run without use of shell (this can avoid to have to shell quote variables):

.. code-block:: yaml

    script:
      - title: make dist
        cmd: [ "make", !i "REVISION=%(prop:got_revision:-%(src::revision:-unknown)s)s", "dist" ]

Buildbot Steps Batteries
~~~~~~~~~~~~~~~~~~~~~~~~

Buildbot comes with battery included. It has a `tons of steps <http://docs.buildbot.net/latest/manual/cfg-buildsteps.html>`_ in it that you could use.
What if you could contruct those steps in the bbtravis.yml?
Guess what? You can.

.. code-block:: yaml

    script:
      - condition: TESTS=='trial'
        step: !Trial
            name: trial
            tests: buildbot.test

Every Buildbot steps from the buildbot.plugins.steps module is available by default.
If you want to use your own customs steps, you can do it with 2 methods.

- Create a buildbot `plugin <http://docs.buildbot.net/latest/manual/plugins.html#plugin-infrastructure-in-buildbot>`_.
  If it is installed in your master virtual environment and recognised inside buildbot.plugins.steps, it will be available in buildbot_travis yaml parser.

- If you want to define your custom step in your master.cfg directly, you will need to register your step directly in the yaml parser.

.. code-block:: python

    from buildbot_travis.travisyml import registerStepClass

    class FancyStep(steps.ShellSequence):
        ...

    registerStepClass("FancyStep", FancyStep)

then in your yaml:

.. code-block:: yaml

    script:
      - step: !FancyStep

.. note::

   You can construct your steps either with arg list or keyword args, but not both e.g following are equivalent

.. code-block:: yaml

    script:
      - step: !ShellCommand "true"

      - step: !ShellCommand
            - "true"

      - step: !ShellCommand
            command: "true"

.. note::

   Due to the way steps are initialized, ``title`` key cannot be used to override the default step name.
   You have to use the standard ``name`` step argument to specify it:

    .. code-block:: yaml

        script:
          - step: !ShellCommand
                command: "true"
                name: "always succeed"

.. note::

   You can also contruct your step list without passing through the dictionary structure

    .. code-block:: yaml

        script:
          - !ShellCommand
                command: "true"
                name: "always succeed"

Status context
~~~~~~~~~~~~~~

If github_token is specified, bbtravis will create a github status for each of the builds of the matrix, with direct link to the sub build.
The name of the status (aka context) is calculated using ``reporter_context`` of the project configuration.
The default is ``"bb%(prop:matrix_label:+/)s%(prop:matrix_label)s"``.

``matrix_label`` is computed by the Trigger step, and is the concatenation of key and values of the matrix.
because matrix can be large, and github context is limited in size, bbtravis implements a way for projects to define abbreviations for the labels.
e.g .bbtravis.yml such as:

.. code-block:: yaml

    language: python

    label_mapping:
      TWISTED: tw
      SQLALCHEMY: sqla
      SQLALCHEMY_MIGRATE: sqlam
      latest: l
      python: py

Will generate context like:  ``bb/py:2.6/sqla:l/sqlam:0.7.1/tw:11.1.0``

.. note::

    context reporter is for now only implemented from github, but it should be easy to adapt to Gitlab, Gerrit, etc

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

A ``Deploy`` section is available in the left side menu. In this section, a Deployment dashboard will be
available once configured.

This dashboard enables a streamlined, fully automated delivery process, from Commit to Production environment.
Latest version of your project is just one click away from users.

See the dashboard's template below

    ==============   =========    =========    =========    =========
     DELIVERABLES                         STAGES
    --------------   ------------------------------------------------
     (projects)        COMMIT        DEV          QA           PROD
    ==============   =========    =========    =========    =========
     Deliverable A    GIT rev      1.2.3        GIT tag      GIT tag
    ==============   =========    =========    =========    =========

For example, the version 1.2.3 (specified thanks to a GIT tag) of deliverable A is deployed in DEV stage.

Here are the 5 steps to setup a Deployment dashboard in Buildbot Travis.

1) A ``Deployment`` section is available in the ``Settings`` section.
   In this section, the ``Deployment Environment(s)`` is the list of target environments (or Stages)
   where deliverables are going to be deployed.
   These environments should be sorted following your development process definition.
   Example::

       COMMIT (merged dev), DEV, QA, PROD
       BEWARE!The first column is reserved for COMMIT stage so you do not need to define it in the Stages list.

2) Go to the ``Deploy`` section in the left side menu. You should see a Deployment dashboard like the above example.
   The Stages should be the same as the ones defined in 1).

3) Go to the ``Settings/Projects`` section. Add corresponding Stages to the different projects in the Stages field.
   Stages can be a subset of the Stages defined in 2).

4) You should see a fully configured Deployment dashboard with all the deliverables, Stages, GIT revisions and GIT
   tags. GIT revisions and GIT tags are available in dropdown lists. When you select a specific version, a pop_up
   window appears to launch the deployment procedure in the specific stage.

5) To enable push button deployments, you need to define the deployment procedures.
   Create deployment scripts and update the script and/or after_script sections of the ``.travis.yml`` file
   of each deliverable.

   Example::

    after_script:
       - |
         # Deployment
           python ./deploy.py --repo "${repository}" --stage "${stage}" --version "${version}";

           ${repository} is the URL of the project's (or deliverable's) repo.
           ${stage} is the retrieved from the Deployment dashboard.
           ${version} is retrieved from the Deployment dashboard.

Configuring Travis Defaults
===========================

The YAML file or Python dict passed to ``TravisConfigurator`` supports a few keys to set some environment defaults.

Default Matrix
--------------
The ``default_matrix`` key contains the default values for any keys the repository's ``.travis.yml`` does not specify.

Example::

    default_matrix:
      os: linux
      dist: debian_7
      language:
        python: 2.7
        c:
          compiler: gcc
        c++:
          compiler: g++

This example sets the default ``os`` to ``linux``, the default ``dist`` to ``debian_7``, and sets default values for three languages.
If the ``.travis.yml`` has ``language: c``, then it will have ``compiler`` set to ``gcc``.

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


CommandLine
===========
``buildbot_travis`` package comes with a ``bbtravis`` command line utility.

This utility is useful to test travis.yml locally without pushing it to the CI.
It allows to test either the travis.yml and the docker image used to run the workers.
It allows to run only the part of the matrix that you are working on

Example::

    bbtravis run -d tardyp/metabbotcfg  -j8 TESTS=trial TWISTED=latest

This will run the resulting tests in parallel using docker image tagged tardyp/metabbotcfg and will filter only the matrix environment with TESTS=='trial' and TWISTED=='latest'

UI is using urwid console UI framework, and will split the terminal into several terminal showing each matrix run.
You can scroll using mouse wheel, and click to zoom and get more details.

.. Note::

    For now ``bbtravis`` command line utility to note support Buildbot step battery nor Interpolate contructs

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


And configure your hyper keys in the default hyper worker
You should also configure an authentication plugin in order to protect those keys.
