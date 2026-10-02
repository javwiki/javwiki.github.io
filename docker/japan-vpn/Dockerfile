FROM alpine:3.22 AS dashboard
ARG CLASH_FOR_LINUX_REF=42c26d8ad44373980ef3e6c4113de3beedb3d876
RUN apk add --no-cache git unzip \
    && git init /upstream \
    && git -C /upstream remote add origin https://github.com/wnlen/clash-for-linux.git \
    && git -C /upstream fetch --depth 1 origin "$CLASH_FOR_LINUX_REF" \
    && git -C /upstream checkout --detach FETCH_HEAD \
    && unzip /upstream/resources/dashboard/dist.zip -d /dashboard

FROM metacubex/mihomo:v1.19.23 AS core
FROM python:3.12-alpine3.22
RUN apk add --no-cache ca-certificates \
    && pip install --no-cache-dir PyYAML==6.0.3 \
    && adduser -D -u 10001 proxy \
    && mkdir -p /data && chown proxy:proxy /data
COPY --from=core /mihomo /usr/local/bin/mihomo
COPY --from=dashboard /dashboard/dist /opt/dashboard
COPY --from=dashboard /upstream/LICENSE /opt/licenses/clash-for-linux-LICENSE
COPY entrypoint.py /opt/entrypoint.py
ENV SAFE_PATHS=/opt/dashboard
USER proxy
EXPOSE 7890 9090
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c 'import socket; socket.create_connection(("127.0.0.1", 7890), 3).close()'
ENTRYPOINT ["python", "/opt/entrypoint.py"]
