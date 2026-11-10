# Development roadmap

The [complete original request](PROJECT_REQUEST.md) is the scope authority.
The owner explicitly authorized Phase 2 on 2026-11-10. Later phases remain planning
records. Backups and storage encryption were explicitly deferred.

| Phase | Work and exit gate | Status |
| --- | --- | --- |
| 1 | Native Hermes identity/memory, Qwen OAuth, Photon owner access, voice, daily briefings, Linux supervision, encrypted backup and reboot validation | Local package ready; live acceptance pending |
| 2 | Gmail OAuth read/search/drafts with approval before send; Google Calendar with approval before mutations; persistent confirmed tasks/commitments/reminders; read-only GitHub and grounded research | In progress: personal tasks and read-only Gmail/Calendar deployed via Composio; owner confirmed calendar/task briefing from chat; task create/complete acceptance, GitHub/research and external-write approval gates remain |
| 3 | Shared document ingestion/retrieval, reading progress/highlights/notes and Bible study with licensed texts, clear interpretive distinctions and source-grounded references | Not started |
| 4 | Separate SQLite financial truth, migrations, auditable ledger/import originals/corrections/reconciliation, budgets/reports, subscriptions/renewals/prices | Not started; real payments disabled |
| 5 | Shopping comparisons/official checkout preparation, isolated authenticated transaction approval and idempotent payment service; simulations for expiry/change/decline/duplicates, security review, then separately authorized supported live payments | Not started; live execution disabled |

Future schema groups: profile/preferences, tasks/commitments/schedules/conversation
references; reading materials/progress/highlights/study plans/notes/reflections;
financial accounts/transactions/ledger/receipts/subscriptions/charges; purchases,
approvals, attempts and audit records. Use foreign keys, WAL, migrations, indexes
and transactional boundaries. Keep finance logically separate from general memory.
Do not introduce empty Phase 2–5 tables into Phase 1 as evidence of implementation.

Future skills: subscription-manager, personal-bookkeeper, shopping-assistant,
payment-approval, reading-companion, bible-study, commitment-tracker,
email-assistant, calendar-assistant, github-assistant, research-assistant and
personal-memory. Phase 1 installs only daily-briefing; native memory is reused.
Every future skill needs purpose, activation, tasks, integrations, tool permissions,
validation, errors, security restrictions, examples and acceptance criteria.

Browser follow-up: the owner identified Simular Box as a browser tool, not as
Bailey’s host. Evaluate its MCP integration in a later approved phase; it is not
installed or enabled in the restricted Phase 1 runtime.
