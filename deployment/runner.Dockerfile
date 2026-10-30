# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

WORKDIR /opt/sentinelle
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir ".[test]" \
    && groupadd --gid 10001 sentinelle \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin sentinelle

USER 10001:10001
WORKDIR /bundle
ENTRYPOINT ["sentinelle-run"]
