# Base image for Python tasks. Pinned so every run sees the same toolchain.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends patch git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pytest==8.3.3

WORKDIR /workspace
