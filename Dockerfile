FROM mysterysd/wzmlx:latest

# qBittorrent upgrade: static qbittorrent-nox 5.2.x (libtorrent 2.0.x). Override with --build-arg.
ARG QBIT_TAG=release-5.2.3_v2.0.13
ARG TARGETARCH

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

RUN set -e; \
    case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
      arm64|aarch64) A=aarch64 ;; \
      *) A=x86_64 ;; \
    esac; \
    if curl -fsSL "https://github.com/userdocs/qbittorrent-nox-static/releases/download/${QBIT_TAG}/${A}-qbittorrent-nox" -o /tmp/qbittorrent-nox; then \
      install -m 755 /tmp/qbittorrent-nox /usr/bin/qbittorrent-nox; \
    else echo "WARN: qbit download failed, keep base image qbittorrent-nox"; fi; \
    rm -f /tmp/qbittorrent-nox; qbittorrent-nox --version || true

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]
