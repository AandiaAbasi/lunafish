FROM node:22-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip build-essential libssl-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages -i https://mirror.abrha.net/repository/pypi/simple --trusted-host mirror.abrha.net pysocks

ENV ALL_PROXY=socks5h://172.17.0.1:1082
ENV HTTP_PROXY=socks5h://172.17.0.1:1082
ENV HTTPS_PROXY=socks5h://172.17.0.1:1082
ENV MEDIASOUP_SKIP_WORKER_PREBUILT_DOWNLOAD=true
ENV MEDIASOUP_BUILDTYPE=Release

COPY package*.json ./
RUN npm install --omit=dev || \
    (cd node_modules/mediasoup && \
     sed -i "s|source_url.*openssl.*|source_url = 'https://www.openssl.org/source/openssl-3.0.8.tar.gz'|" worker/subprojects/openssl.wrap && \
     sed -i "/patch_url/d" worker/subprojects/openssl.wrap && \
     sed -i "/patch_hash/d" worker/subprojects/openssl.wrap && \
     sed -i "/patch_filename/d" worker/subprojects/openssl.wrap && \
     cd /app && npm install --omit=dev)

FROM node:22-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/node_modules ./node_modules
COPY . .

EXPOSE 3001
CMD ["node", "server.js"]
