#!/usr/bin/env bash
# Root-only rollout: validate current release, test staging, archive, then apply with rollback.
set -euo pipefail
umask 077
[[ $EUID == 0 ]] || { echo 'Run as root on the existing box' >&2; exit 2; }
staging=${1:?Provide the root-owned staging directory}
[[ -d "$staging" && ! -L "$staging" ]] || exit 2
set -a
source /etc/bailey/runtime.env
set +a
export PYTHONPATH="/opt/bailey:$HERMES_SOURCE"
run_bailey() {
  sudo -u bailey env HERMES_HOME="$HERMES_HOME" HERMES_PYTHON="$HERMES_PYTHON" \
    PYTHONPATH="$PYTHONPATH" "$@"
}
run_bailey "$HERMES_PYTHON" -m bailey.runtime_check
(
  cd "$staging"
  export PYTHONPATH="$staging:$HERMES_SOURCE"
  run_bailey "$HERMES_PYTHON" -m unittest discover -s tests -q
  run_bailey /home/bailey/.local/bin/hermes plugins validate "$staging/plugins/bailey_productivity"
  run_bailey "$HERMES_PYTHON" "$staging/deploy/check-write-contracts.py"
)
archive=$(mktemp -d /data/home/bailey-phase2-rollout.XXXXXX)
cp -a /opt/bailey "$archive/code"
mkdir "$archive/profile"
for name in config.yaml .env bailey-profile.json bailey-initial-config.json SOUL.md skills; do
  cp -a "$HERMES_HOME/$name" "$archive/profile/$name"
done
rollback() {
  trap - ERR
  echo 'Rollout failed; restoring the previous code and profile' >&2
  cp -a "$archive/code/." /opt/bailey/
  for name in config.yaml .env bailey-profile.json bailey-initial-config.json SOUL.md; do
    cp -a "$archive/profile/$name" "$HERMES_HOME/$name"
  done
  mv "$HERMES_HOME/skills" "$archive/failed-skills"
  cp -a "$archive/profile/skills" "$HERMES_HOME/skills"
  systemctl restart bailey-gateway
  exit 1
}
trap rollback ERR
systemctl stop bailey-gateway
cp -a "$staging/." /opt/bailey/
run_bailey "$HERMES_PYTHON" /opt/bailey/deploy/apply-phase2-update.py
run_bailey "$HERMES_PYTHON" -m bailey.runtime_check
systemctl restart bailey-gateway
systemctl is-active --quiet bailey-gateway
trap - ERR
echo 'Phase 2 proposal update activated; external writes executed: 0'
