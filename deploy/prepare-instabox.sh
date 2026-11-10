#!/usr/bin/env bash
# Keep the existing /home/bailey deployment paths on InstaBox's persistent disk.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run as root inside the existing InstaBox.' >&2; exit 1; }
mountpoint -q /data || { echo '/data must be mounted.' >&2; exit 1; }
if id bailey >/dev/null 2>&1 || [[ -e /home/bailey ]]; then
  echo 'Existing Bailey account/home found; inspect before relocating it.' >&2
  exit 1
fi
install -d -m 0700 /data/bailey /home/bailey
mount --bind /data/bailey /home/bailey
if ! grep -q '^/data/bailey /home/bailey ' /etc/fstab; then
  printf '%s\n' '/data/bailey /home/bailey none bind,x-systemd.requires-mounts-for=/data 0 0' >> /etc/fstab
fi
bash /opt/bailey/deploy/bootstrap-vps.sh
chown bailey:bailey /home/bailey
install -d -m 0755 /etc/systemd/system/bailey-gateway.service.d
cat > /etc/systemd/system/bailey-gateway.service.d/storage.conf <<'EOF'
[Unit]
RequiresMountsFor=/home/bailey

[Service]
ExecStartPre=/usr/bin/mountpoint -q /home/bailey
EOF
systemctl daemon-reload
echo 'Persistent Bailey home and dedicated account prepared. Gateway not activated.'
