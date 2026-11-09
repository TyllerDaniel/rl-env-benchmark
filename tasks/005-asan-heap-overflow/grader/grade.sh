#!/bin/sh
# Hidden grader for the C task. Builds the agent's strbuf.c against our tests
# with AddressSanitizer and UBSan; any memory error fails the run.
set -eu

out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

cc -std=c11 -Wall -Wextra -g -O1 \
   -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all \
   -Isrc src/strbuf.c "$GRADER_DIR/test_hidden_strbuf.c" -o "$out/hidden"

# Leak detection needs ptrace, which some container runtimes block.
ASAN_OPTIONS=detect_leaks=0:abort_on_error=0 "$out/hidden"
