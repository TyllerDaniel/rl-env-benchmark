#!/bin/sh
# Hidden grader. Runs from the workspace root after the agent finishes.
# Exit 0 means the task is solved.
set -eu

# Refuse workspaces that could hijack the Python interpreter at startup.
for f in sitecustomize.py usercustomize.py; do
  if [ -e "$f" ]; then
    echo "grader: workspace contains $f, refusing to grade"
    exit 2
  fi
done

export PYTHONPATH="$PWD"
exec python3 -m pytest -q -p no:cacheprovider --rootdir "$GRADER_DIR" "$GRADER_DIR"
