#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HERMES_PYTHON:?Set HERMES_PYTHON to the installed Hermes dependency environment Python}"
: "${HERMES_SOURCE:?Set HERMES_SOURCE to the official Hermes source checkout}"
export HERMES_HOME=/home/bailey/data
export PYTHONPATH="/opt/bailey:$HERMES_SOURCE"
cd /home/bailey
case "${1:-}" in
  check) exec "$HERMES_PYTHON" -m bailey.runtime_check ;;
  check-offline) exec "$HERMES_PYTHON" -m bailey.runtime_check --offline ;;
  schedules) exec "$HERMES_PYTHON" -m bailey.schedules ;;
  database) exec "$HERMES_PYTHON" -m bailey.acceptance ;;
  *) echo 'Usage: run-helper.sh check|check-offline|schedules|database' >&2; exit 2 ;;
esac
