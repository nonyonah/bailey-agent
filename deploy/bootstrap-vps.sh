#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 && $(uname -s) == Linux ]] || { echo 'Run as root on Debian/Ubuntu Linux.' >&2; exit 1; }
apt-get update
apt-get install -y ca-certificates curl git python3 ffmpeg restic
if ! id bailey >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash bailey
fi
# bailey gets no sudo, administrative group, payment secrets, or inbound web ports.
install -d -m 0755 /opt/bailey /etc/bailey
install -d -o bailey -g bailey -m 0700 /home/bailey/data
install -d -m 0700 /var/lib/bailey-backup
echo 'Copy this project to /opt/bailey (root-owned); then follow README as bailey.'
