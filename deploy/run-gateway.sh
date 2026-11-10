#!/usr/bin/env bash
set -euo pipefail
/opt/bailey/deploy/run-helper.sh check
exec /home/bailey/.local/bin/hermes gateway run
