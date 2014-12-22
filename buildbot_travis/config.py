from twisted.python import log


class Sadface:
    brdict = None


def nextBuild(builder, requests):
    """
    This nextBuild function stops builds from having a spawner fire up
    if there are no free builders
    """

    if not builder.builder_status:
        log.msg("nextBuild: Builder %s does not have a builder_status" %
                builder)
        return Sadface()

    job = builder.master.getStatus().getBuilder("%s-job" % builder.name)
    for slavename in job.slavenames:
        slave = builder.master.botmaster.slaves[slavename]
        if not slave.canStartBuild():
            continue
        if hasattr(slave, "substantiation_deferred") and slave.substantiation_deferred:
            continue

        # it looks like the job builder might have some slots available
        return requests[0]

    log.msg(
        "nextBuild: Tried to start spawner '%s' but not jobs slots available" % builder.name)
    return Sadface()
