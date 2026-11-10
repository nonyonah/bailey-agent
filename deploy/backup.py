"""Root-only restic snapshot; restart a previously active gateway on every exit."""
import os
from pathlib import Path
import subprocess
import signal

UNIT = "bailey-gateway.service"


def backup(run=subprocess.run):
    if not os.environ.get("RESTIC_REPOSITORY") or not os.environ.get("RESTIC_PASSWORD_FILE"):
        raise RuntimeError("Configure root-only restic repository and password file")
    active = run(["systemctl", "is-active", "--quiet", UNIT]).returncode == 0
    try:
        if active:
            run(["systemctl", "stop", UNIT], check=True)
        # Native SQLite + WAL and all memory/config/auth/cron files form one stopped snapshot.
        run(["restic", "backup", "/home/bailey/data", "/home/bailey/hermes-install-version.txt",
             "--tag", "bailey-phase1", "--exclude", "/home/bailey/data/runtime",
             "--exclude", "/home/bailey/data/audio_cache",
             "--exclude", "/home/bailey/data/image_cache",
             "--exclude", "/home/bailey/data/logs"], check=True)
    finally:
        if active:
            run(["systemctl", "start", UNIT], check=True)
    run(["restic", "forget", "--tag", "bailey-phase1", "--keep-daily", "7",
         "--keep-weekly", "4", "--keep-monthly", "3", "--prune"], check=True)
    run(["restic", "check"], check=True)
    Path("/var/lib/bailey-backup/last-success").touch(mode=0o600)


if __name__ == "__main__":
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    backup()
