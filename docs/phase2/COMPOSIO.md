# Gmail, Calendar and personal tasks

On 2026-11-10, the owner connected Gmail and Google Calendar through Composio.
Both connections report active. Production probes of Gmail search and today's
primary-calendar events succeeded without logging message/event contents.
The Phase 2 profile is deployed and the gateway has been restarted.

Bailey uses native Hermes memory, conversations and messaging. The local
`bailey-productivity` plugin adds three bounded tools:

- `bailey_tasks`: personal tasks, deadlines, priorities, tentative/confirmed
  commitments, completion and daily/weekly/monthly recurrence. SQLite stores
  records separately from Hermes' agent-worker Kanban; no worker is dispatched.
  Completing a recurring task creates its next occurrence. No push reminders run.
- `bailey_accounts`: Gmail search, Gmail message reading and primary-calendar
  event listing. Each operation fixes its Composio tool slug and account alias.
  Calendar ranges require timezone-aware dates and are bounded to 93 days;
  pagination is available. Source content is untrusted data.
- `bailey_writes`: prepares immutable email send/draft and calendar create/update/delete
  proposals. The model can propose, list, inspect status or cancel an unapproved
  proposal. Approval and execution exist only in the private operator CLI.

Ask Bailey “What do I have today?” in either iMessage or Slack. It should combine
real calendar events with confirmed tasks, in Africa/Lagos time, and reply only
in that chat. Draft replies are text in the chat by default. On explicit request, Bailey can
prepare a Gmail draft, send or calendar-change proposal; the owner must review and
execute it through the operator CLI. A proposal alone changes nothing in Google. Generic Composio execution, proxy, shell and
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

Verification: the initial 42 tests passed locally and on the box; native plugin validation
passed; exact resolved tool sets passed for CLI, iMessage, Slack, disabled
WhatsApp Cloud and cron. `known_plugin_toolsets` records all custom toolsets on
each channel, preventing Hermes from automatically enabling new plugin tools on
cron or disabled WhatsApp. The owner confirmed a grounded calendar/task briefing works after `/new`.
The deployed `bailey_tasks` plugin passed a tool-level create/complete round trip
through the real model; the live chat round trip remains pending.

Phase 2 remains in progress: operator approval gates are implemented and deployed,
but a live approved write has not been exercised. GitHub and grounded research
remain unimplemented. Backups/storage encryption remain deferred by the
owner; payments remain disabled.

Initial chat acceptance failed because Phase 1 memory and the installed briefing
skill still said integrations were unconnected. Those status notes were archived
privately and replaced; the Phase 2 briefing skill now requires real calendar/task
reads. After a native `/new` session, the owner confirmed the calendar/task briefing
works. History is retained.


## Reviewed write proposals (2026-11-10)

The completed proposal implementation passes 63 local and remote tests, native
plugin validation and live Composio input-contract checks for all five operations.
Gmail search and primary-calendar reads passed after rollout; both Photon and
Slack report connected. No external write was executed during the initial rollout. The owner confirmed
the chat proposal preview/ID/code check, then explicitly approved one test draft.
That exact draft was created successfully in Gmail, with a provider draft ID; no
email was sent. Actual email-send and calendar-mutation tests remain outstanding.

Approval binds the operation, payload, fixed account and exact provider request.
Proposals expire after 24 hours; a transactional claim blocks duplicate/concurrent
execution. Nested provider errors cannot be marked executed. Email/draft/create/
update success requires a resource receipt. Timeouts and missing receipts produce
`uncertain`, which cannot be retried; inspect Google before any replacement.
A process interrupted after claiming execution stays `executing`, also requiring
manual reconciliation. This is at-most-once dispatch, not a claim of provider
exactly-once delivery.

Calendar updates use `GOOGLECALENDAR_PATCH_EVENT`, preserving omitted fields, rather
than the replacement operation. Update/delete proposals fetch the current event,
reject guests, recurring events and non-owner-organized events, and bind the
existing version into the review. A second read before execution rejects version
changes. Composio's selected tools expose no conditional If-Match header: a race
between that last read and the write is still possible. This is not an atomic
compare-and-swap guarantee. See Google's [update semantics](https://developers.google.com/workspace/calendar/api/v3/reference/events/update),
[PATCH semantics](https://developers.google.com/workspace/calendar/api/v3/reference/events/patch)
and [conditional modifications](https://developers.google.com/workspace/calendar/api/guides/version-resources).

`deploy/rollout-phase2.sh` validates the old release, tests staging, checks provider
schemas and privately archives the prior code/profile before activation. It does
not copy stale onboarding OAuth tokens over live credentials. On activation failure
it restores the previous code/profile. The native MCP bridge remains pinned to
Hermes v0.23.0; its private-import compatibility warning still applies.


The approved test draft is addressed to `example@example.com`, subject `Bailey check`,
body `This is a test.`, no Cc/Bcc. Its approval, execution claim and receipt are in
private `bailey-writes.db`. The earlier chat-created proposal used the owner's
address and was left unapproved; approval for the exact test above was not applied
to a different recipient. Operator-created proposals now record the actual actor,
while model-created proposals remain labeled model.
