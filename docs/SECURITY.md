# Phase 1 security

## Enforced configuration

One E.164 owner number is configured both as Photon allowlist and briefing target.
Allow-all is false. Group messages require a mention matching `(?!)`, which never
matches; verify the installed adapter's gate during acceptance. No regex is a
substitute for the owner allowlist. Telemetry is off. The Photon sidecar uses its
native random per-start token and binds loopback only; port 8789 stays firewalled.

An exact reviewed config is checked before gateway startup. Unexpected dotenv
keys, endpoint overrides, alternate MCP servers, tools, permissive flags and public
secret permissions block startup. Runtime inspection calls the installed Hermes
tool resolver; only memory, session_search and text_to_speech are permitted. Cron
uses its own explicit smaller list. Native CLI setup/scheduling is performed by
the operator, not exposed as an agent tool. No payment service or credentials exist.

The runtime/identity instructions reject instructions embedded in external content.
Prompt-injection protection is layered: small tool surface, no generic execution,
no browser, no connector authentication and no unrestricted file tool. Prompt text
alone does not guarantee protection. The model can still produce incorrect or
inappropriate text; verify critical information. Future browser access changes the
threat model and requires a new review.

## Secrets and storage

Hermes auth.json contains refresh/device tokens; .env contains Photon/Groq secrets.
Native memory and state.db can contain personal conversations. Directories use
0700 and files 0600 under a dedicated unprivileged OS account. At-rest encryption
must come from the VPS's encrypted volume/LUKS; SQLite WAL is not encryption.
The deployment explicitly requires an operator confirmation before activation.

OAuth scopes and token refresh are owned by the native Qwen/Photon login. No email,
calendar, GitHub or payment scopes are requested. Service root credentials and
backup secrets stay in root-only /etc/bailey, outside the agent's readable profile.
The bailey account cannot use sudo. Root-owned operations code cannot be rewritten
by the agent. Do not add SSH agent forwarding or unrelated cloud keys to this user.

The official installer/source and provider services are trusted dependencies.
Record versions, inspect update diffs, rerun runtime policy and acceptance checks.
No unattended updates. Stable installer and inspected main can differ: incompatibility
blocks activation rather than widening the allowlist.

## Backups, retention and audit

Restic encrypts/authenticates backups. A stopped gateway gives a consistent snapshot
of native SQLite, WAL, memory, auth, configuration and schedules. Restic secrets are
separate; an offline recovery password is essential. Retention is seven daily,
four weekly and three monthly snapshots. Backups intentionally omit runtime tokens,
generated audio/image cache and file logs. Imported attachments elsewhere in the
profile remain included. Review storage usage and retention for your actual workload.

Session retention is configured as 90 days. This is not an assurance that every
cache, media file, backup or provider copy is erased at that time. Native journal
and cron receipts provide operational evidence, not a tamper-proof financial audit.
No new content audit database is introduced before it is needed. Set host journal
limits, protect access, and never paste raw logs into public bug reports.

Memory deletion is separate from session and backup deletion. For complete erasure,
stop the gateway, use the installed Hermes session-management commands to remove
the relevant history, review media/cache, prune affected backups according to your
policy, and consider provider-side retention. Never delete rows directly from the
native database while Hermes is running. See operations for the operator workflow.

## Known limits

The gateway process itself must access its native auth tokens. Hosted Photon,
Qwen, Groq and Edge are data processors, so this is private single-owner deployment,
not offline processing. The same OS user can change its own profile; policy checks
catch drift at startup, not host compromise while running. Interactive owner slash
commands remain upstream functionality; do not treat an authorized owner as an
untrusted tenant. Protect the owner's Apple account and VPS SSH credentials.

Authorization rejection, group blocking, live token refresh, actual provider data
handling and reboot recovery remain untested until the live checklist passes.
Payments remain disabled in Phases 1–4. Phase 5 must introduce a separate authenticated
approval/execution service, starting in simulation; chat/voice text cannot authorize it.

## Current owner decisions

Only one Slack member and one iMessage phone number are authorized. Never add
another identity without the owner's explicit instruction. Slack stays enabled.
The reported second-sender test matched the configured owner identity, so it is
not evidence of a bypass and does not satisfy the live rejection criterion.
Backups and storage encryption are explicitly deferred; neither is represented
as configured or verified. The guest uses direct ext4 disks; provider encryption
at rest is unverified.
