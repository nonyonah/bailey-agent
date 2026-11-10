#!/usr/bin/env bash
# Runs privately on the box; never put credentials in command arguments.
set -euo pipefail
set -a
source /etc/bailey/runtime.env
set +a
export PYTHONPATH="/opt/bailey:$HERMES_SOURCE"
/home/bailey/.local/bin/hermes whatsapp-cloud
"$HERMES_PYTHON" -m bailey.upgrade_channel --home "$HERMES_HOME" --enable-whatsapp
/opt/bailey/deploy/run-helper.sh check
echo 'Both channel profiles are ready. Tell the operator to finish the HTTPS webhook and restart the existing gateway.'
