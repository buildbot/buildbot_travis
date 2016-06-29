FROM buildbot/buildbot-master:master
COPY example /usr/src/buildbot_travis/example

RUN \
    apk add --no-cache py-cffi py-requests docker-py@testing && \
    pip install 'txrequests' 'pyjade' 'txgithub' 'ldap3' 'docker-py>=1.4' && \
    pip install /usr/src/buildbot_travis/example/*.whl && \
    rm -r /root/.cache

WORKDIR /var/lib/buildbot
VOLUME /var/lib/buildbot
CMD ["/usr/src/buildbot_travis/example/start_buildbot.sh"]
