# Base image for C tasks: gcc with AddressSanitizer/UBSan runtimes, gdb and make.
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev make gdb patch git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
