# Operating Bailey

Use `/home/bailey/data` as HERMES_HOME consistently. All CLI commands below run as
`bailey` with `/etc/bailey/runtime.env` exported unless labelled root.

## Routine checks

```bash
hermes photon status
hermes cron list
hermes cron status
hermes cron doctor
/opt/bailey/deploy/run-helper.sh check
/opt/bailey/deploy/run-helper.sh database
```

As root inspect `systemctl status bailey-gateway bailey-health bailey-backup` and
`journalctl -u bailey-gateway -n 100`. Treat logs as private. The health timer
checks process state and the authenticated Photon stream endpoint, not the model
or recipient delivery. A failed health unit is a local alert; there is no separate
email/SMS notification in Phase 1. Inspect backup `last-success` and snapshot history.

## Backups

The timer runs at approximately 03:00 Lagos, with up to five minutes jitter. Root
can trigger `systemctl start bailey-backup.service`. It stops the gateway, backs
up personal state using restic, and restarts a previously running gateway even if
backup fails. An intentionally stopped gateway stays stopped. Gateway downtime is
the duration of the snapshot; pruning/check run after restart. A SIGKILL, kernel
failure or power loss can bypass cleanup; systemd restarts the gateway on reboot.
Check service status after any interrupted backup. Do not manually start or change
the profile during a snapshot. Only one systemd backup service runs at a time.

The package retains no backup password inside the agent home. Use root's exported
backup.env and RESTIC_PASSWORD_FILE to inspect `restic snapshots` and `restic check`.
These must pass against the real repository before claiming backups work. Never
publish output containing private paths or backend details.

## Restore drill and disaster recovery

1. On a recovery VPS, prepare the dedicated account, encrypted storage, root-only
   repository credentials/password, and the same recorded Hermes release. Keep
   the gateway stopped (`systemctl stop bailey-gateway.service`).
2. Export the root backup environment, set RESTIC_PASSWORD_FILE, run `restic snapshots`,
   then `restic restore SNAPSHOT_ID --target /var/lib/bailey-backup/restore`.
   Inspect the restored tree privately. Do not restore into the live profile.
3. Preserve the old profile separately with mode 0700. Copy the restored
   `home/bailey/data` into `/home/bailey/data`; preserve the entire DB plus `-wal`
   and `-shm` if present. Do not combine files from different snapshots. Restore the
   install-version record separately. Correct ownership to bailey:bailey and verify
   directories are 0700 and credential/config files 0600.
4. Runtime records are excluded. Remove any stale runtime/lock data only with the
   service stopped and after consulting the installed Hermes recovery guidance.
   Ensure the recorded code version and Python path match `/etc/bailey/runtime.env`.
5. Run the profile/runtime check and read-only SQLite integrity/WAL check as bailey.
   Root starts the gateway. Native SQLite handles WAL recovery. Inspect cron
   receipts and paused jobs; uncertain deliveries should not be blindly replayed.
6. Send an authorized iMessage, confirm recall of a harmless pre-backup fact, test
   audio, and trigger one briefing. Record evidence in ACCEPTANCE.md. Reauthenticate
   native OAuth only if required; old tokens may have been revoked or expired.

Test this on a separate disposable recovery machine or directory before relying
on the backup. Do not point a restored test profile at Photon simultaneously with
production; two gateways can create confusing or duplicate delivery.

## Updates

Take and verify a backup first. Root stops the gateway; as bailey, keep code/runtime
installation in its original install home and use the native `hermes update` flow.
Do not use `pip install -U` on arbitrary Hermes dependencies. Record the new Hermes
version/commit, review upstream changes affecting Photon/auth/tools/cron, update
the dependency Python path if PM selected a new generation, then rerun checks.
Reapply the reviewed Phase 1 config only after reviewing wizard migrations. Restart
and repeat sender, voice, memory, schedule and reboot checks. Preserve old runtime
and state together for rollback; do not point an older binary at a newly migrated
SQLite database without upstream compatibility guidance.

## Memory inspection and deletion

Ask Bailey to show or remove a particular saved memory and verify the native tool
result. Inspect memories/USER.md and MEMORY.md privately; root may stop the gateway
for direct edits to avoid races. A deletion from memory does not delete historical
chat or backups. Consult `hermes sessions --help` for the installed version's history
management commands before removing history, and verify those commands with its
official documentation. Review restored backups, media and provider retention when
fulfilling a complete erasure request. Never place passwords or payment information
in identity/memory files.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Gateway refuses startup | Exact policy, private permissions, required secrets, installed Python/dependencies and actual tool definitions. Do not widen the allowlist to silence errors. |
| Model login works in CLI but gateway fails | Same HERMES_HOME and bailey user; refresh Qwen OAuth through native hermes model; then verify/reset reviewed config. |
| No iMessage | Native Photon status, device approval, project credentials, owner E.164 allowlist, opted-in first message, and live sidecar health. |
| Briefing exists but does not arrive | Running gateway/sidecar, exact home recipient, first-message opt-in, timezone, cron status and separate delivery errors. |
| Voice note fails | GROQ_API_KEY/quota or local Whisper install/model, FFmpeg, supported audio and 20 MB cap; inspect privately and request typed input. |
| Image/document cannot be understood | Attachment transport is distinct from extraction/vision. Qwen model may lack image support; general document tools are deliberately off. |
| Repeated service failure | Fix underlying issue, then root resets failed state and restarts; inspect journal without exposing credentials. |
| Backup failure | Repository reachability, host key, root-only credentials/password, free space, restic locks and service restart; do not forcibly unlock an active writer. |
| Missed/uncertain cron fire | Inspect native status/receipts, make an operator decision before resume/retry. Reconcile never silently resumes paused jobs. |

## Current exceptions and voice runtime

The owner deferred encrypted backups on 2026-11-10. No repository, password or
backup timer has been configured. This is an accepted omission, not a passing
restore test. Do not run the full activation wrapper until its independent gates
are satisfied or explicitly revised.

Native Hermes extras `slack`, `stt-whisper`, and `edge-tts` were installed through
Hermes PM. `/etc/bailey/runtime.env` now points at the environment containing all
three. HF_HOME is `/home/bailey/data/cache/huggingface` so model cache writes stay
within the service sandbox. Local Whisper uses small. Raw tools are exposed
directly rather than deferred behind tool search; the allowed tool set remains
memory, session_search and text_to_speech. Human voice checks are still open.
