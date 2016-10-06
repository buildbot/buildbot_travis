# please follow docker best practices
# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/

FROM tardyp/buildbot-master
COPY example /usr/src/buildbot_travis/example

RUN \
    apk add --no-cache \
        py-cffi \
        py-openssl \
        py-requests && \
    pip install buildbot_travis && \
    rm -r /root/.cache

EXPOSE 8010
EXPOSE 9989

CMD ["/usr/src/buildbot_travis/example/start_buildbot.sh"]
