FROM alpine:3.19

ARG UID
ARG GID

HEALTHCHECK --interval=20s --timeout=10s --retries=3 --start-period=30s CMD ! supervisorctl status | grep -v RUNNING
ENTRYPOINT ["/bin/sh", "/opt/hydrus/static/build_files/docker/client/entrypoint.sh"]
LABEL git="https://github.com/hydrusnetwork/hydrus"

RUN apk --no-cache add supervisor opencv mpv mpv-libs ffmpeg jq libheif \
 openssl nodejs patch font-noto font-noto-emoji font-noto-cjk \
 py3-pyside6 py3-beautifulsoup4 py3-pillow py3-numpy py3-openssl py3-cryptography py3-pip py3-opencv py3-lxml py3-chardet \
 py3-psutil py3-pysocks py3-requests py3-twisted py3-yaml py3-lz4 py3-html5lib py3-dateutil py3-qtpy py3-mpv py3-service_identity
RUN apk --no-cache add build-base python3-dev fribidi-dev harfbuzz-dev jpeg-dev lcms2-dev openjpeg-dev libjpeg-turbo-dev libheif-dev
RUN apk --no-cache add xorg-server xorgxrdp xrdp xfce4 xcb-util-cursor-dev xhost
RUN pip install --break-system-packages Send2Trash cloudscraper pyparsing cbor2 Pympler pillow-heif dateparser

COPY static/build_files/docker/client/xrdp/xrdp.ini /etc/xrdp/
COPY static/build_files/docker/client/xrdp/sesman.ini /etc/xrdp/
COPY static/build_files/docker/client/xrdp/startwm.sh /etc/xrdp/
RUN chmod a+x /etc/xrdp/startwm.sh
COPY static/build_files/docker/client/xrdp/start-xrdp.sh /etc/xrdp/
RUN chmod a+x /etc/xrdp/start-xrdp.sh
#RUN xhost +si:localuser:root

RUN set -xe \
    && mkdir -p /opt/hydrus \
    && addgroup -g 1000 hydrus \
    && adduser -h /opt/hydrus -u 1000 -H -S -G hydrus hydrus

COPY --chown=hydrus . /opt/hydrus
COPY --chown=hydrus --from=suika/swftools:2013-04-09-1007 /swftools/swfrender /opt/hydrus/bin/swfrender_linux
RUN mv /opt/hydrus/static/build_files/docker/client/supervisord.conf /etc/supervisord.conf

RUN adduser rdp -D
RUN echo "rdp:rdp" | chpasswd

RUN ln -fs /usr/bin/python3 /usr/bin/python && ln -fs /usr/bin/pip3 /usr/bin/pip

VOLUME /opt/hydrus/db

ENV QT_SCALE_FACTOR=1.1 \
    VNC_PORT=5900 \
    NOVNC_PORT=5800 \
    SUPERVISOR_PORT=9001 \
    XVFBRES=1680x1050x24 \
    UID=${UID:-1000} \
    GID=${GID:-1000} \
    DB_DIR=/opt/hydrus/db \
    XVFB_EXTRA="" \
    VNC_EXTRA="" \
    NOVNC_EXTRA="" \
    HYDRUS_EXTRA=""

EXPOSE 5800 5900 3389
