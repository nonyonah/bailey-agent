# Bailey — private Hermes personal assistant

Bailey uses **Nous Research Hermes Agent**, hosted on the existing InstaBox Free
machine `box-1dcd5f`. The primary interface is **iMessage via Photon**.
iMessage is primary and **Slack is the working manual fallback**, with private
owner-only DMs. Real AI replies are verified on both. WhatsApp and Telegram are disabled. See
[Slack setup](docs/SLACK.md) for the app manifest and private token entry.

**Phase 1 remains in progress.** Hermes v0.23.0 is installed on persistent storage.
The updated owner number is registered with Photon; opt-in and a real two-way AI conversation are verified. OpenRouter free inference and structured tool
calling passed. The owner confirmed improved transcription in both channels and playable audio.
Automatic process restart and full reboot persistence/reconnection passed.
Remaining security acceptance checks are tracked in docs/ACCEPTANCE.md.
Backups are deferred by explicit owner preference. Payments are
disabled. **Phase 2 is in progress:** persistent personal tasks and read-only Gmail/Calendar
through Composio are deployed. See [Phase 2 setup and limits](docs/phase2/COMPOSIO.md).
Phases 3–5 have not started.

The full scope is preserved in [the original request](docs/PROJECT_REQUEST.md).
Current setup: [InstaBox and iMessage onboarding](docs/INSTABOX.md).
See [architecture](docs/ARCHITECTURE.md), [security](docs/SECURITY.md),
[operations/recovery](docs/OPERATIONS.md), [acceptance](docs/ACCEPTANCE.md), and
[the roadmap](docs/ROADMAP.md).

## What Bailey reuses

Hermes owns the agent loop, native memory, SQLite conversations, skills, cron,
transcription, audio replies and the Photon adapter. This project provides
configuration and operations helpers, not a second agent framework.

- Identity: `$HERMES_HOME/SOUL.md`; owner/context: `memories/USER.md` and `MEMORY.md`.
- Structured session history: native `state.db`, checked read-only for integrity/WAL.
- Model: `openrouter/free`, with free-provider availability and request limits.
- Voice: local Faster-Whisper small model, with native dependencies installed;
  optional Groq configuration remains supported. Edge TTS on explicit request.
- Briefings: ask “What do I have today?” in either chat. Automatic morning/evening
  cron jobs are paused; replies stay in the requesting chat.
- Restricted tools: memory, session search, TTS, personal tasks and read-only Gmail/Calendar;
  cron only memory/search.
- Supervision: dedicated unprivileged bailey account and hardened systemd units.
- Backups: root-only, encrypted off-host restic snapshots; configure and restore-test.

## Hosting behavior and costs

The owner accepts InstaBox Free's idle pauses and runtime cap. Local schedules and
health checks cannot execute while paused. An InstaBox HTTPS request can wake an
auto-paused box, but cannot remove maximum-run cooldowns. Account limits can change:
inspect `instabox get box-1dcd5f --json` rather than assuming a fixed cap.

Photon uses its managed iMessage connection and a local supervised sidecar.
No public webhook is needed. An inbound iMessage does not wake a paused box;
reconnection and missed-message behavior still require live testing.

OpenRouter free inference has quotas and variable model availability. No paid
fallback is configured. Local transcription uses CPU/RAM; Edge TTS is online.
Hosted messaging/model/TTS providers receive relevant data. Off-host backup storage
may incur costs. File permissions and WAL do not encrypt a disk: verify at-rest
volume encryption before storing live credentials/activating the service.

## Existing-box setup

The dedicated `/home/bailey` home is bind-mounted from persistent `/data/bailey`.
The storage drop-in prevents the gateway starting without its mount. Cold-boot
persistence still needs validation. Code is root-owned under `/opt/bailey`.

For a fresh InstaBox only, `deploy/prepare-instabox.sh` performs this storage/account
setup. It refuses an existing home to avoid relocating it accidentally. For a generic
Debian/Ubuntu VPS use `deploy/bootstrap-vps.sh`. Do not repeat either on this box.

The official installer wrapper is `deploy/install-hermes.sh`; Hermes itself is
already installed. Version/commit are recorded in `~/hermes-install-version.txt`.
Use official updates with a verified backup; never auto-upgrade dependencies.

## iMessage onboarding

The existing Photon login and project are retained. The owner's replacement number
was registered on 2026-11-10 and applied to both the allowlist and briefing target.
The owner must send one blue iMessage from that number to the newly assigned Bailey
line to complete Photon's opt-in. See INSTABOX.md for current routing status.

For new deployments only, initialize an empty profile with:

```bash
export PYTHONPATH=/opt/bailey
python3 -m bailey.profile init --home "$HERMES_HOME" --phone YOUR_E164_OWNER_NUMBER --stt local
```

For the existing profile use `bailey.upgrade_channel` after credential setup, as
shown in INSTABOX.md. It archives config privately, preserves credentials/history,
sets the correct Photon recipient and disables other messaging adapters. It does
not initialize another agent or rewrite native memory.

## Validate and activate

`/etc/bailey/runtime.env` records the actual Hermes interpreter/source paths.
Load it as bailey using `set -a; source /etc/bailey/runtime.env; set +a`, then:

```bash
/opt/bailey/deploy/run-helper.sh check-offline
/opt/bailey/deploy/run-helper.sh check
```

The offline check verifies policy and installed APIs without proving credentials.
The normal check additionally requires Photon project credentials and a native OpenRouter credential. The gateway always uses the normal
check. Exact config drift, unknown environment overrides and unexpected tools block
startup; discovery wrappers are checked against the full underlying tool catalog.

Before activation, root must configure `/etc/bailey/backup.env`, a restic password
file, an initialized off-host repository and verified encrypted storage. Instructions
and recovery are in OPERATIONS.md. Then root runs `deploy/activate.sh`.

Keep the Photon sidecar on loopback. No public messaging port is required.

With the gateway running, register native schedules as bailey:

```bash
/opt/bailey/deploy/run-helper.sh schedules
hermes cron list
hermes cron status
hermes cron doctor
```

The reconciliation helper now pauses legacy Bailey briefing jobs and never creates
or resumes schedules. The owner replaced 08:00/20:00 pushes with on-demand requests.
Ask “What do I have today?” or “What is left today?” in either chat; replies stay in
that chat. Slack is a manual fallback, not automatic failover or message mirroring.
Calendar, email and task integrations are not connected, so current briefings use
only confirmed memory and conversations.

## Tests and acceptance

```bash
python3 -m unittest discover -s tests -v
for script in deploy/*.sh; do bash -n "$script" || exit; done
```

Twenty-nine local tests cover owner restrictions, endpoint/config drift, secret
permissions, credential-preserving migration, schedules, SQLite and backup-failure
recovery. All 29 tests and the installed-Hermes credential/tool policy check passed on the
box after the iMessage migration. Fixtures are tests only.
The live sender, voice, messaging, reboot and restore checks are listed
in ACCEPTANCE.md; configuration existence is not live evidence.
