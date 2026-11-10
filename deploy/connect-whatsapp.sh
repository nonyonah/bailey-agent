#!/usr/bin/env bash
# Run in the owner's terminal so Meta credentials stay out of chat and history.
set -euo pipefail
if [[ ! -t 0 || ! -t 1 ]]; then
  echo 'Run this command in your own interactive terminal.' >&2
  exit 1
fi
command -v instabox >/dev/null || { echo 'InstaBox CLI is required.' >&2; exit 1; }
exec instabox ssh box-1dcd5f --no-paste -- -t \
  'sudo -iu bailey bash /opt/bailey/deploy/configure-whatsapp.sh'
