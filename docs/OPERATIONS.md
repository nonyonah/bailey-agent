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
| Model login works in CLI but gateway fails | Same HERMES_HOME and bailey user; refresh Nous Portal OAuth through native hermes model; then verify/reset reviewed config. |
| Model calls fail with 401/429, or gateway refuses startup on credentials | Nous Portal free-tier limit or a credential marked failed by an upstream error. Inspect `hermes auth list nous`, run `hermes auth reset nous` after confirming the credential is intact, and re-authenticate with `hermes auth add nous --type oauth --no-browser` if needed. Keep `auxiliary.free_only: true`; wait for the free-tier reset. Do not buy credits without owner approval. |
| No iMessage | Native Photon status, device approval, project credentials, owner E.164 allowlist, opted-in first message, and live sidecar health. |
| Briefing exists but does not arrive | Running gateway/sidecar, exact home recipient, first-message opt-in, timezone, cron status and separate delivery errors. |
| Voice note fails | GROQ_API_KEY/quota or local Whisper install/model, FFmpeg, supported audio and 20 MB cap; inspect privately and request typed input. |
| Image/document cannot be understood | Attachment transport is distinct from extraction/vision. The selected Nous free model may lack image support; general document tools are deliberately off. |
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

The Nous Portal free account is subject to free-tier request limits. An earlier
OpenRouter route exhausted its free-models-per-day limit during Phase 2 testing on
2026-11-10 and marked the pooled credential auth-failed, blocking the gateway
pre-start credential check. Bailey now uses Nous Portal OAuth with
`upstage/solar-mini4:free`; `hermes auth reset nous` clears a failed credential and
`hermes auth add nous --type oauth --no-browser` re-authenticates if required.
Reviewed configuration keeps `auxiliary.free_only: true` so background auxiliary
calls cannot silently use a paid OpenRouter model.


## Review and execute Gmail/Calendar proposals

Load the private runtime environment and run as `bailey`, with
`PYTHONPATH=/opt/bailey:$HERMES_SOURCE` and `HERMES_HOME=/home/bailey/data`.
Use `$HERMES_PYTHON /opt/bailey/deploy/approvals.py` with:

```text
list
show PROPOSAL_ID
approve PROPOSAL_ID --confirm APPROVAL_CODE
execute PROPOSAL_ID --confirm APPROVAL_CODE
reject PROPOSAL_ID --note "Reason"
events PROPOSAL_ID
```

Review `show` first, including full To/Cc/Bcc, subject/body or the complete calendar
preview and existing event version. Approval expires with the proposal after 24h.
Approval alone changes nothing. Run execute only for the reviewed, specifically
authorized action. The model cannot approve or execute through its tools.
After deployment the owner approved one test Gmail draft, which saved successfully.
Live email-send and calendar-mutation acceptance remains outstanding.

`uncertain` or `executing` requires checking Gmail/Calendar before doing anything
else. Never blindly retry, reset the row, or create a replacement send to work
around the terminal state. A network timeout may occur after Google accepted the
operation. `failed` records an explicit provider/preflight rejection; review it
before deciding whether a fresh proposal is appropriate. Receipts are compact
resource IDs, not full email/event response bodies. Calendar version preflight
is not an atomic conditional write; see phase2/COMPOSIO.md for the remaining race.
