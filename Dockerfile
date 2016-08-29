FROM buildbot/buildbot-master:master
COPY example /usr/src/buildbot_travis/example

RUN \
    apk add --no-cache py-cffi py-requests docker-py@testing && \
    pip install 'txrequests' 'pyjade' 'txgithub' 'ldap3' 'docker-py>=1.4' 'hyper-compose' && \
    pip install /usr/src/buildbot_travis/example/*.whl && \
    rm -r /root/.cache

EXPOSE 8010
EXPOSE 9989
WORKDIR /var/lib/buildbot
VOLUME /var/lib/buildbot
CMD ["/usr/src/buildbot_travis/example/start_buildbot.sh"]
