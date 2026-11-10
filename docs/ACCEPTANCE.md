# Phase 1 evidence

Local validation date: 2026-11-10. Live deployment: **pending**.
Do not mark a checkbox from configuration existence alone. Record runtime version,
date/time, redacted evidence and any limitations beside each live result.

## Local implementation

- [x] Official docs and relevant source inspected; architecture/plan recorded.
- [x] Bailey identity and native memory paths prepared.
- [x] Restricted model/Photon/voice configuration and cron skill prepared.
- [x] Official installer wrapper, supervision, health and backups prepared.
- [x] 29 automated local tests passed (stdlib unittest).
- [x] Bash script syntax checks passed.
- [x] Installed stable Hermes v0.23.0 runtime compatibility test on Linux (offline; no credentials/model call).
- [x] systemd-analyze verify passed on the target Linux host.

Tests cover phone validation, owner-target consistency, allow-all rejection,
permissions/symlinks, unreviewed endpoints, tool/config drift, missing credentials,
local STT option, idempotent job reconciliation, paused/duplicate/error cases,
read-only SQLite/WAL checks, and restart after backup failure. Test fixtures do not
represent working integrations. Systemd unit definitions and the installed Hermes tool catalog were subsequently
verified on the existing InstaBox. Restic backup execution remains untested. OpenRouter free inference and structured
tool calling passed on 2026-11-10. The Linux helper suite also passed all 29 tests.

## Hosting adjustment accepted by owner

InstaBox Free is selected. Continuous uptime and guaranteed delivery at 08:00/20:00
are waived for this deployment. Automatic briefing pushes were subsequently
replaced by owner-requested on-demand replies; both legacy jobs are paused. Validate
pause/resume, Photon reconnection, memory persistence and missed-fire handling.
Record asleep/missed briefings explicitly rather than counting them as delivered.
UptimeRobot is optional and not configured. Other security/voice/recovery criteria
remain required.

## Live acceptance gate

- [ ] VPS encrypted volume confirmed; SSH-only firewall; bailey has no sudo.
- [ ] Hermes version/commit and dependency Python recorded; runtime check passes.
- [x] OpenRouter free account completes a real inference and structured tool-call probe.
- [x] Saved model credentials reused after supervised gateway restart; real Slack reply verified.
- [x] Photon project ready; replacement owner number registered and opt-in verified live.
- [x] Owner confirmed receiving a real AI reply through iMessage on the replacement number.
- [ ] Another number's DM is rejected without model access or private disclosure.
- [ ] Group messages (including ones containing "Bailey" or "Hermes") produce no response.
- [ ] Small text+attachment message preserves text and media; unsupported media is explained.
- [x] Owner confirmed real voice-note transcription in both Slack and iMessage after the small-model upgrade.
- [ ] A corrupt/unsupported voice note produces a useful failure response in chat.
- [ ] Mixed voice/text context and default-text behavior explicitly checked.
- [x] Owner confirmed audio playback in both channels and a new requested audio reply after the direct-tool fix.
- [x] Native memory/config hashes unchanged across process recovery and full reboot; a fresh-session recall test remains separate.
- [x] Native state.db integrity and WAL verified; a real Photon conversation is persisted.
- [x] Owner superseded scheduled pushes with on-demand briefings in either chat.
- [x] Both legacy morning/evening jobs confirmed paused through native cron API.
- [x] Owner confirmed “What do I have today?” receives an AI reply in Slack.
- [x] Reconciliation does not create/resume briefing jobs; unrelated jobs are preserved.
- [ ] On-demand briefing tested in iMessage; no invented commitments or cross-channel duplicate.
- [x] SIGKILL of the idle main process triggered systemd restart; both transports reconnected.
- [x] Full guest reboot changed boot ID, restored home bind mount, gateway and both transports, and preserved memory/config/database. Automatic briefings remain paused by preference.
- [ ] Local health check detects stopped/degraded sidecar and recovers after native reconnect.
- [ ] Real restic snapshot/check succeeds; stopped profile restores with memory/SQLite intact.
- [ ] Backup failure recovery tested on target; no permanent unintended gateway outage.
- [ ] Prompt-injection attachment cannot expose credentials or enable execution tools.
- [ ] Payment request via text/voice/reaction is refused; runtime has no payment-capable tools.
- [ ] No payment credentials/services or Phase 2–5 integration tokens installed.

**Stop here until all Phase 1 acceptance criteria pass.** Any failure remains an
explicit outstanding item; do not start Phase 2 just because local tests pass.

On 2026-11-10 the owner returned to Photon with a replacement number. Registration,
private profile migration, Linux tests and live credential/tool policy checks passed.
First-message opt-in is verified live. The supervised gateway and loopback sidecar
are running. The owner confirmed receiving both the connection test and a real AI reply.

Live messaging evidence: owner confirmed receipt of the outbound connection test.
The next owner iMessage reached a Photon session and produced an OpenRouter free
assistant response (one model API call, no logged error). The owner confirmed AI-reply receipt, and Hermes reports the reply delivered. Two native briefing jobs were reconciled to Photon; next-run
and actual briefing deliveries remain acceptance checks.

Dual-channel update: 26 tests passed locally and on Linux. Photon remains live.
WhatsApp is prepared but disabled pending Meta credentials and resolution of the
owner-reported Business account restriction; no WhatsApp live acceptance is claimed.

Slack supersedes the WhatsApp second-channel plan. All 29 local/Linux tests and
the installed-Hermes restricted policy check passed. Slack dependencies installed;
app credentials and real Slack/Photon coexistence checks remain pending.

Latest live evidence (2026-11-10): Slack and Photon state connected after fixing
the service's writable native state directory. Slack user confirmed a real reply;
native Slack delivery state is delivered. Both legacy jobs have enabled=false and
state=paused. All 29 tests pass locally and on Linux. Phase 2 is not yet cleared.

Voice correction (2026-11-10): the owner corrected their initial “both worked”
report: accent transcription was inaccurate and no playable audio was delivered on
either channel. Human voice/playback remain unverified. Native test audio generation,
local transcription of a synthetic sentence and corrupt-audio rejection passed
under service filesystem restrictions. Whisper was changed from base to small.
No TTS calls existed in either chat history; the three reviewed tools are now
exposed directly with tools.tool_search.enabled=off and explicit audio-tool usage
instructions. Runtime policy and 30 tests pass. Human retesting is required.

Backups are explicitly deferred by the owner. Do not mark encrypted backup/restore
as passed or block other authorized work on configuring a backup destination.
Storage encryption and reboot recovery remain separate unresolved checks.

Latest voice/recovery results: owner confirmed test audio arrived in Slack after
initially not finding it, confirmed the upgraded transcription works in both
channels, and confirmed a new requested audio reply plays. Slack API file metadata
shows a hosted audio/mpeg test attachment. Native allowlist matching and impossible
mention-pattern probes passed; these are not live second-sender/group tests.
After SIGKILL, systemd NRestarts=1, both platforms connected, native memories and
configuration hashes unchanged, conversation rows preserved, SQLite integrity ok.
Gateway boot activation and the existing Photon health timer are now enabled;
the health service ran successfully. The local Slack-aware monitor edit has not
been deployed (its upload was declined); current periodic health checks do not
independently prove Slack delivery. Full reboot verification passed.

Full reboot evidence: boot ID changed, gateway active, /home/bailey bind-mounted,
memory/config SHA-256 unchanged, conversation row count preserved, SQLite integrity
ok, Photon and Slack connected. The owner confirmed a correct post-reboot channel/briefing reply, except for
a stale Slack credential-status note; that exact native USER.md note was corrected
and the gateway reloaded.
At-rest disk encryption is unverified; the guest ext4 mount and public provider
documentation reviewed do not establish host-level encryption. No encryption
attestation file was fabricated. Backup/restore remains explicitly deferred.

Context recall after reboot: the owner confirmed Bailey remembered iMessage as
primary, Slack as fallback and on-demand briefings. A stale “Slack pending private
app credentials” note and old scheduled-briefing sentence in USER.md were replaced
with the verified current state, preserving unrelated memories and a private copy.

Owner decisions (2026-11-10): storage encryption is deferred alongside backups.
Guest inspection found ext4 directly on vda/vdb, with no guest encryption mapping;
host-level encryption was not established by public provider documentation.
Neither encryption nor backups is marked passed.

The reported Slack rejection test was sent under the configured allowed member ID,
as shown by the nonce-bearing native session. It therefore does not establish an
authorization bypass or a successful rejection of another identity. Slack was
briefly disabled during investigation and restored at the owner's request; both
channels report connected, with one allowed Slack member and one iMessage number.
The owner explicitly requires owner-only access and no additions without instruction.
A genuine different-sender rejection remains unverified.

Phase 2 (2026-11-10): Composio Gmail and Calendar connections active. Bounded
production Gmail search and primary-calendar read probes succeeded. Personal task
plugin and account tools deployed; gateway restarted. 42 local/remote tests, native
plugin validation (private-MCP-API warning) and exact per-channel tool policy passed.
Tasks are excluded from cron and disabled WhatsApp via known_plugin_toolsets.
Email sending/calendar editing/generic Composio tools remain unavailable. Human
grounded-briefing and persistent-task chat checks are pending. Phase 2 remains
in progress; see phase2/COMPOSIO.md.

Phase 2 chat acceptance update (2026-11-10): after the stale integration notes
and briefing skill were replaced and the owner started `/new`, the owner confirmed
Bailey successfully checked calendar and tasks from chat. Grounded on-demand
briefing acceptance passed. A persistent task create/complete chat round trip,
GitHub/research and external-write approval gates remain outstanding.
