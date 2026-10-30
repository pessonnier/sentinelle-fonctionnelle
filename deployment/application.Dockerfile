# syntax=docker/dockerfile:1.7
FROM python:3.12.11-slim-bookworm

WORKDIR /opt/sentinelle
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir "." \
    && groupadd --gid 10000 sentinelle \
    && useradd --uid 10000 --gid 10000 --no-create-home --shell /usr/sbin/nologin sentinelle \
    && mkdir -p /var/lib/sentinelle \
    && chown 10000:10000 /var/lib/sentinelle

USER 10000:10000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
ENTRYPOINT ["sentinelle-fonctionnelle"]
CMD ["serve", "--host", "0.0.0.0", "--database", "/var/lib/sentinelle/sentinelle.db"]
