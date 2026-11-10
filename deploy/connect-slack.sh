#!/usr/bin/env bash
set -euo pipefail
[[ -t 0 && -t 1 ]] || { echo 'Run in your own interactive terminal.' >&2; exit 1; }
exec instabox ssh box-1dcd5f --no-paste -- -t \
  'sudo -iu bailey bash /opt/bailey/deploy/configure-slack.sh'
