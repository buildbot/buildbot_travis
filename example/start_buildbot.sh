#!/bin/sh
B=`pwd`
if [ ! -f $B/buildbot.tac ]
then
    bbtravis create-master $B
    cp /usr/src/buildbot_travis/example/buildbot.tac $B
fi
# wait for pg to start by trying to upgrade the master
until buildbot upgrade-master $B
do
    sleep 1
done
exec twistd -ny $B/buildbot.tac
