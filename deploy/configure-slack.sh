#!/usr/bin/env bash
set -euo pipefail
set -a
source /etc/bailey/runtime.env
set +a
export PYTHONPATH="/opt/bailey:$HERMES_SOURCE"
"$HERMES_PYTHON" -m bailey.setup_slack
/opt/bailey/deploy/run-helper.sh check
