# InstaBox hosting assessment

Checked 2026-11-09 against [official documentation](https://instabox.sh/).
The owner created `box-1dcd5f`; the local CLI is authenticated. Inspected live:
Debian/systemd, 4 vCPU, 8 GiB RAM, 20 GiB persistent `/data`, 30-minute idle pause,
and account-specific runtime limits (120 minutes on Nov 9; 480 minutes on Nov 10).
Read current limits from `instabox get`; do not assume a fixed cap.
A dedicated bailey user and persistent home bind mount are prepared; Hermes
**v0.23.0**, commit `2bd378ed1b`, is installed. All 21 helper tests pass on Linux;
installed tool-catalog/API checks and systemd unit verification pass. Nous Portal OAuth is saved in the native pool. The supervised gateway is running
for live messaging. Storage encryption verification, off-host backups and permanent
boot activation remain pending.

The owner selected **InstaBox Free**, accepting intermittent availability in place
of the original 24/7 requirement. Use it for Phase 1 without upgrading the account.
Bailey responds while the machine is awake. Validate Photon reconnection and iMessage delivery after resume and distinguish a queued delivery
from a confirmed reply.

Use the existing box; do not create another machine:

```bash
instabox get box-1dcd5f --json
instabox ssh box-1dcd5f
```

Keep the free plan's pause/runtime settings. For an auto-paused machine, use
`instabox wake box-1dcd5f`; explicitly paused/stopped machines require `instabox resume
box-1dcd5f` / `instabox start box-1dcd5f` respectively. Verify status before connecting.
See [runtime settings](https://instabox.sh/docs/machines/auto-pause).

The owner replaced automatic 08:00/20:00 pushes with on-demand briefings in either
chat. Both old jobs are paused. A request still requires an awake VM.
The same limitation affects local health checks and backup timers.

UptimeRobot is optional and is not configured. An HTTP monitor would need a
published health endpoint, separate from the messaging transport. Its requests
may wake an auto-paused machine, but cannot remove maximum-run limits or cooldowns.
Start with manual wake and assess actual usage first. Never publish port 8789 or
Hermes control endpoints for monitoring.

InstaBox documents Debian microVMs and a persistent `/data` volume. Before adapting
deployment, verify systemd, sudo/root access, volume encryption, reboot behavior,
outbound Photon connectivity, and disk persistence. Place Bailey state and runtime
on persistent storage; `deploy/prepare-instabox.sh` bind-mounts `/data/bailey` at `/home/bailey`, preserving
the deployment paths. The gateway drop-in requires that mount. Cold-boot
persistence still needs verification.

The owner number is saved privately in the live profile, both as
PHOTON_ALLOWED_USERS and PHOTON_HOME_CHANNEL. It is not Bailey's assigned Photon line.

## Current channel and account onboarding

The owner returned to **iMessage via Photon** on 2026-11-10 with a replacement
owner number, stored privately in the native profile. WhatsApp and Telegram are
disabled. The old owner number has been replaced in both PHOTON_ALLOWED_USERS and
PHOTON_HOME_CHANNEL; existing credentials, conversations and memories are preserved.

Photon registered the new number and assigned Bailey a new shared line. The owner
must send a blue iMessage from the new number to that line; the assigned line was
provided in chat and is available through `hermes photon status`. Opt-in was verified live after the owner sent the first message. The old assigned line must not be assumed valid.

The operator applied `bailey.upgrade_channel` and verified the installed Hermes
credential and restricted-tool checks. All 21 tests passed locally and on the box.
Photon opt-in is now verified. The supervised gateway was installed and started
for live messaging checks; boot activation and backup timers remain deferred.
The local sidecar health check passed and Photon accepted an outbound test message.
The owner confirmed the connection-test receipt. Their subsequent iMessage
reached the model and generated a persisted assistant response. The owner confirmed
receipt, and the native delivery record reports delivered.
No Meta credentials or public WhatsApp webhook are needed for the selected channel.
`deploy/connect-whatsapp.sh` is retained only for a future explicit channel change.

Check status privately:

```bash
instabox ssh box-1dcd5f
sudo -iu bailey
export HERMES_HOME=/home/bailey/data
export PATH="$HOME/.local/bin:$PATH"
hermes photon status
```

Photon uses an outbound managed connection; its sidecar stays on loopback. Public
HTTP traffic is not part of iMessage delivery and inbound messages cannot wake the
paused guest. Scheduled delivery and reconnect behavior need live acceptance.

## Model authentication correction

Nous Portal OAuth **is saved in the native credential pool**. `hermes auth list
nous` confirmed one credential, without revealing its value. Qwen CLI v0.27.1 removed
the legacy free command Hermes v0.23.0 recommends, so the owner selected the Nous
Portal free tier instead. No Qwen subscription was purchased.

Real Nous Portal free-tier inference and structured tool calling passed on
2026-11-10 with `upstage/solar-mini4:free`; no tool action was executed by that
isolated model probe.

## Second channel requested

On 2026-11-10 the owner requested both iMessage and official WhatsApp Business,
using the same private owner number. Dual-channel policy, independent restricted
toolsets, health checks and credential-preserving activation are prepared. All 26
tests passed locally and on Linux; the current Photon gateway stayed active.
Briefings continue through Photon to avoid duplicate notifications.

WhatsApp is still disabled: no Meta credentials are saved, and the owner reports
the WhatsApp Business account is restricted. Do not treat a completed local wizard
as removal of a Meta restriction. Resume the official API setup after Meta permits
messaging; do not replace it with an unofficial bridge.

The private helper remains `bash deploy/connect-whatsapp.sh`. It now preserves
Photon and only enables the additional platform after required credentials exist.
The operator must still validate Meta API access, publish the signed receiver,
complete Meta webhook configuration, restart the existing gateway, and verify both
channels. No public webhook has been published yet.

Both channels use native memory and session search in one Hermes profile, with
separate channel conversations. Changing the authorized iMessage phone number
requires registration, new sender/delivery settings and a fresh Photon opt-in;
the assigned Bailey line may change. Existing memory is preserved. An Apple email
identity is not automatically authorized by the current phone-only policy.

## Current selection: Slack and iMessage

The owner subsequently selected Slack plus iMessage for work. This supersedes the
WhatsApp second-channel plan above. Photon remains live and the owner can install
apps in their Slack workspace. Slack policy, a DM-only app manifest and private
setup helper are installed; 29 tests and runtime policy checks pass on the box.
Native Slack dependencies were installed with Hermes PM. Slack remains disabled
until its app credentials are supplied. WhatsApp and Telegram remain disabled.

See [Slack onboarding](SLACK.md). Briefings remain on Photon. No public webhook is
needed. Do not treat separate Slack threads as automatically sharing the immediate
iMessage conversation; native memory/session search are shared.

## Latest verified behavior

Slack credentials are saved and verified. Both Slack and Photon report connected;
the owner confirmed a real Slack AI reply and native delivery is recorded. Slack
is the manual fallback; iMessage remains primary.

The owner replaced automatic morning/evening pushes with on-demand briefings. Both
legacy jobs are paused and the reconciliation helper will not recreate/resume them.
Ask “What do I have today?” in either chat; use confirmed native memory/history,
state that calendar/email/task services are not connected, and reply in that chat.

The Slack startup failure was a read-only native state-directory error. The service
now permits only the additional `/home/bailey/.local/state/hermes` path, created
private and owned by bailey. Both adapters reconnected successfully afterward.

Phase 2 remains gated by the outstanding Phase 1 voice, backup/restore, security
and restart/reboot acceptance checks. The scheduling criteria are superseded by
the owner's on-demand preference, not treated as incomplete scheduled delivery.

## Voice and recovery progress

The owner confirmed small-model transcription in Slack and iMessage, test-file
playback on both, and a new requested audio response after direct tool exposure.
The voice-capable PM environment and persistent HF_HOME are recorded in runtime.env.
A native service-sandbox synthetic voice round trip and corrupt-file rejection
passed. The owner deferred backups; no backup repository or timer was added.

The gateway and existing local health timer are enabled for boot. SIGKILL recovery
passed with both transports reconnected, memory/config hashes unchanged and SQLite
integrity preserved. Full guest reboot verification passed. At-rest volume
encryption is still unverified; file permissions do not establish it.

The actual reboot changed the kernel boot ID. The gateway auto-started, the home
bind mount returned, both transports connected, memory/config hashes were unchanged,
and persisted conversation rows and SQLite integrity were retained.
