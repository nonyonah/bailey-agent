#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run as root.' >&2; exit 1; }
test -f /etc/bailey/runtime.env
test -f /etc/bailey/backup.env
test -f /etc/bailey/restic-password
test -f /etc/bailey/encrypted-storage-confirmed
# This root file records the operator's verification that the VPS data volume is
# encrypted; it is an attestation, not an automatic disk-encryption detector.
chmod 600 /etc/bailey/backup.env /etc/bailey/restic-password
chmod 644 /etc/bailey/runtime.env
chown -R root:root /opt/bailey
chmod -R go-w /opt/bailey
install -m 0644 /opt/bailey/deploy/systemd/bailey-* /etc/systemd/system/
install -m 0644 /opt/bailey/deploy/logrotate /etc/logrotate.d/bailey
install -d -o bailey -g bailey -m 0700 /home/bailey/.local/state/hermes
systemctl daemon-reload
systemctl enable --now bailey-gateway.service
systemctl enable --now bailey-health.timer bailey-backup.timer
echo 'Services enabled; run the live acceptance checklist before calling Phase 1 validated.'
