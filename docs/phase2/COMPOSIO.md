# Gmail, Calendar and personal tasks

On 2026-11-10, the owner connected Gmail and Google Calendar through Composio.
Both connections report active. Production probes of Gmail search and today's
primary-calendar events succeeded without logging message/event contents.
The Phase 2 profile is deployed and the gateway has been restarted.

Bailey uses native Hermes memory, conversations and messaging. The local
`bailey-productivity` plugin adds two bounded tools:

- `bailey_tasks`: personal tasks, deadlines, priorities, tentative/confirmed
  commitments, completion and daily/weekly/monthly recurrence. SQLite stores
  records separately from Hermes' agent-worker Kanban; no worker is dispatched.
  Completing a recurring task creates its next occurrence. No push reminders run.
- `bailey_accounts`: Gmail search, Gmail message reading and primary-calendar
  event listing. Each operation fixes its Composio tool slug and account alias.
  Calendar ranges require timezone-aware dates and are bounded to 93 days;
  pagination is available. Source content is untrusted data.

Ask Bailey “What do I have today?” in either iMessage or Slack. It should combine
real calendar events with confirmed tasks, in Africa/Lagos time, and reply only
in that chat. Email drafts are text in the chat; sending email and editing
calendar events are unavailable. Generic Composio execution, proxy, shell and
workbench tools are never exposed to the model. Google consent may grant broader
provider permissions than Bailey's tool surface; this is an application-level
restriction, not a claim that the OAuth scopes themselves are read-only.

Native Hermes stores Composio OAuth tokens privately under `mcp-tokens`. Account
onboarding used a separate private profile, then copied only the native Composio
credential files to the live profile. No Google Cloud client JSON is required.
The manual GOOGLE_SETUP guide remains an unused alternative.

The plugin uses private Hermes MCP bridge APIs because the current plugin API
has no equivalent bounded-call interface. Hermes is pinned to v0.23.0; runtime
policy checks and account probes must pass before upgrading. Hermes' own plugin
validator passes with a warning about these private imports. No Hermes core
source is modified.

Verification: 42 tests passed locally and on the box; native plugin validation
passed; exact resolved tool sets passed for CLI, iMessage, Slack, disabled
WhatsApp Cloud and cron. `known_plugin_toolsets` records all custom toolsets on
each channel, preventing Hermes from automatically enabling new plugin tools on
cron or disabled WhatsApp. The owner confirmed a grounded calendar/task briefing works after `/new`.
A persistent task create/complete chat round trip remains pending.

Phase 2 remains in progress: external-write approval gates, GitHub and grounded
research are not implemented. Backups/storage encryption remain deferred by the
owner; payments remain disabled.

Initial chat acceptance failed because Phase 1 memory and the installed briefing
skill still said integrations were unconnected. Those status notes were archived
privately and replaced; the Phase 2 briefing skill now requires real calendar/task
reads. After a native `/new` session, the owner confirmed the calendar/task briefing
works. History is retained.
