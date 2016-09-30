FROM buildbot/buildbot-master:master
COPY example /usr/src/buildbot_travis/example

RUN \
    apk add --no-cache py-cffi py-requests docker-py@testing && \
    pip install buildbot_travis && \
    rm -r /root/.cache

EXPOSE 8010
EXPOSE 9989
WORKDIR /var/lib/buildbot
VOLUME /var/lib/buildbot
CMD ["/usr/src/buildbot_travis/example/start_buildbot.sh"]
