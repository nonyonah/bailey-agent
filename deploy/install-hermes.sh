#!/usr/bin/env bash
set -euo pipefail
umask 077
if [[ $(id -un) != bailey || $(uname -s) != Linux ]]; then
  echo 'Run on the Linux VPS as the dedicated bailey user.' >&2
  exit 1
fi
# Keep code/runtime in the default install home, personal state separately in ~/data.
unset HERMES_HOME
installer=$(mktemp)
trap 'rm -f "$installer"' EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
  https://hermes-agent.nousresearch.com/install.sh -o "$installer"
bash "$installer" --non-interactive --skip-browser --skip-computer-use
mkdir -p "$HOME/data"
chmod 700 "$HOME/data"
"$HOME/.local/bin/hermes" --version > "$HOME/hermes-install-version.txt"
git -C "$HOME/.hermes/hermes-agent" rev-parse HEAD >> "$HOME/hermes-install-version.txt"
echo 'Hermes installed. Follow README authentication and runtime verification before activation.'
