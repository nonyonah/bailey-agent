# Build My Personal AI Assistant Using Hermes Agent

You are a senior AI engineer, systems architect, and full-stack developer. Your task is to build a private, cloud-hosted personal AI assistant using the open-source **Hermes Agent by Nous Research**.

This is a real implementation project, not a prototype, mockup, or conceptual demonstration.

The assistant should be capable of managing my daily life, work, communications, finances, subscriptions, learning, and approved online purchases. It should operate continuously in the cloud and communicate primarily through iMessage.

**Important:** Do not build a new agent framework from scratch. Use Hermes Agent's existing architecture, memory, skills, scheduling, tool execution, and integrations wherever possible. Extend it only when necessary.

Before implementing anything, inspect the current Hermes Agent repository and its official documentation. Verify supported features, configuration formats, installation instructions, CLI commands, and integrations. Do not invent APIs or configuration options.

## 1. Core Technical Decisions

- **Agent framework:** Hermes Agent (Nous Research)
- **Primary interface:** iMessage using Photon
- **Hosting:** Linux VPS, running continuously
- **LLM:** Nous Portal free tier (selected; Qwen OAuth was evaluated but unavailable)
- **Programming language:** Python for Hermes-native integrations; TypeScript/Node.js where appropriate for supporting services
- **Database:** SQLite with WAL mode
- **Memory:** Hermes native memory, supplemented with structured persistent storage
- **Scheduling:** Hermes built-in cron functionality
- **Speech-to-text:** Groq Whisper free tier or local Faster-Whisper
- **Text-to-speech:** Edge TTS or another supported low-cost provider
- **Browser automation:** Hermes native browser tools
- **Integrations:** Official APIs, OAuth, MCP, and custom Hermes skills
- **Payments:** Official merchant checkout with explicit approval before every transaction
- **Timezone:** Africa/Lagos
- **Morning briefing:** 08:00 daily
- **Evening briefing:** 20:00 daily

This assistant is for one person only. Do not implement public registration, team accounts, multi-tenancy, or subscription billing for the assistant itself.

Prioritize free and open-source solutions. Clearly identify any components that require paid infrastructure or have usage restrictions.

## 2. Agent Personality and Identity

Create and configure the appropriate Hermes identity and memory files, including `SOUL.md` and `USER.md`, using their actual supported locations.

The assistant should:

- Communicate naturally, clearly, and concisely.
- Be proactive without sending excessive notifications.
- Remember my preferences, projects, commitments, and previous decisions.
- Ask clarifying questions only when essential.
- Avoid fabricating information or claiming actions were completed when they were not.
- Distinguish confirmed information from assumptions.
- Adapt its responses based on context.
- Offer recommendations and challenge weak reasoning constructively.
- Respect my privacy and personal boundaries.
- Never execute payments without my explicit approval.
- Never expose private credentials or financial information unnecessarily.

It should feel like a capable personal assistant rather than a generic chatbot.

## 3. Phase 1 — Foundation, Memory, iMessage, and Voice

Set up Hermes Agent on a Linux VPS.

### Requirements

1. Install and configure Hermes using the official installation process.
2. Configure a compatible free hosted LLM; Nous Portal free tier is selected.
3. Integrate Photon as the iMessage gateway.
4. Restrict incoming messages to my authorized phone number.
5. Configure Hermes memory and personal identity.
6. Enable persistent conversations across restarts.
7. Implement automatic process restart and basic health monitoring.
8. Configure environment variables and secrets securely.
9. Support incoming text messages and attachments.
10. Support incoming voice notes and transcription.
11. Support optional audio replies.
12. Configure automated morning and evening briefings.
13. Implement encrypted backups for persistent data.
14. Verify that the assistant can recover after a VPS reboot.

### Voice behavior

- Transcribe incoming voice messages automatically.
- Process transcribed requests like normal messages.
- Reply in text by default.
- Generate an audio response when explicitly requested.
- Preserve relevant conversational context across voice and text.
- Handle unsupported audio formats gracefully.
- Never interpret a voice instruction as sufficient authorization to execute a financial transaction.

### Scheduled briefings

**Morning — 08:00 Africa/Lagos**

Include:
- Today's calendar events
- Important tasks and deadlines
- Outstanding commitments
- Important emails, once connected
- Project priorities
- Relevant reminders

**Evening — 20:00 Africa/Lagos**

Include:
- Completed tasks
- Outstanding work
- Tomorrow's schedule
- Upcoming deadlines
- Important follow-ups
- Brief suggestions for the following day

Do not invent calendar events, emails, or completed tasks when integrations are not connected.

Ensure scheduled messages are delivered through Photon and use timezone-aware scheduling.

### Phase 1 acceptance criteria

- Hermes responds to authorized iMessages.
- Unauthorized senders cannot access the assistant.
- Conversation context survives restarts.
- Voice messages are transcribed correctly.
- Audio replies work when requested.
- Both briefings are scheduled correctly.
- The assistant recovers after server restarts.
- Payment execution is completely disabled.

## 4. Phase 2 — Productivity, Communication, and Research

Create Hermes skills and integrations for daily productivity.

### Email management

Integrate Gmail using OAuth.

Capabilities:
- Read and summarize emails.
- Identify important messages.
- Search previous correspondence.
- Draft replies.
- Track emails awaiting responses.
- Suggest follow-ups.
- Organize email summaries.

Sending emails requires explicit approval.

### Calendar management

Integrate Google Calendar.

Capabilities:
- Check availability.
- Summarize upcoming events.
- Prepare meeting schedules.
- Identify scheduling conflicts.
- Create reminders.
- Suggest available meeting times.

Creating, modifying, or deleting calendar events requires approval.

### Task and commitment management

Build a persistent task system supporting:
- Task creation
- Due dates
- Priorities
- Recurring reminders
- Task completion
- Overdue notifications
- Commitment extraction from conversations
- Daily and weekly summaries

The assistant should remember commitments made during conversations when appropriate, but distinguish suggestions from confirmed tasks.

### GitHub and project management

Integrate GitHub using least-privilege authentication.

Capabilities:
- Review repositories.
- Summarize recent commits.
- Track issues and pull requests.
- Explain code.
- Identify outstanding development tasks.
- Prepare implementation suggestions.
- Provide project progress summaries.

Do not modify repositories, merge pull requests, or deploy applications without approval.

### Research

Use Hermes's existing research and browser capabilities.

Support:
- Web research
- Product comparisons
- Technical documentation research
- Market research
- Career opportunities
- Company research
- Summaries with source links
- Scheduled research tasks

Prioritize reliable sources and provide citations for important factual claims.

## 5. Phase 3 — Reading Companion and Bible Study

Implement two distinct Hermes skills sharing a document ingestion and knowledge retrieval system.

### Reading Companion

The assistant should help me understand and remember books, articles, research papers, and PDFs.

Capabilities:
- Import supported reading materials.
- Track books and reading progress.
- Explain difficult passages.
- Summarize chapters.
- Identify important arguments.
- Challenge assumptions.
- Compare ideas across books.
- Generate comprehension questions.
- Save highlights and notes.
- Produce weekly reading summaries.
- Remember what I've read.

Use retrieval grounded in the actual source material.

Do not invent quotations, page references, or chapter contents.

Respect copyright and document access restrictions.

### Bible Study Companion

Create a dedicated Bible study skill.

Capabilities:
- Explain Bible passages.
- Provide historical and cultural context.
- Compare translations.
- Find cross-references.
- Explain theological concepts.
- Explore different Christian interpretations.
- Create daily and weekly reading plans.
- Generate reflection questions.
- Track study progress.
- Save study notes.
- Recall previous discussions.

The assistant should distinguish biblical text, historical evidence, theological interpretation, and personal application.

Use properly licensed or public-domain Bible texts.

Do not present contested interpretations as undisputed facts.

### Persistent learning records

Store:
- Reading materials
- Progress
- Highlights
- Notes
- Study sessions
- Bible reading plans
- Reflection entries
- Personal insights

## 6. Phase 4 — Subscription Management and Personal Bookkeeping

Build a personal financial management layer backed by SQLite.

Do not use the language model's memory as the financial source of truth.

### Bookkeeping

Implement:
- Manual income and expense recording
- Bank statement imports (CSV, Excel, PDF)
- Receipt uploads
- Receipt extraction
- Transaction categorization
- Duplicate detection
- Transfer identification
- Refund tracking
- Transaction reconciliation
- Monthly and weekly summaries
- Budget tracking
- Spending insights
- CSV exports

Use an auditable double-entry ledger where appropriate.

Preserve original imported records and maintain a clear history of corrections.

### Subscription Manager

Capabilities:
- Manually register subscriptions.
- Discover recurring payments from financial records.
- Identify subscription receipts in connected email.
- Track billing cycles.
- Track subscription prices and currencies.
- Calculate monthly and annual subscription expenses.
- Send renewal reminders.
- Identify unexpected price changes.
- Assist with subscription cancellations.
- Track payment history.

The assistant should support requests such as:

- "How much am I spending on subscriptions?"
- "When does my YouTube Premium renew?"
- "Remind me before my next renewal."
- "Show my most expensive subscriptions."
- "Help me cancel a subscription."

Do not claim a subscription has been cancelled until its cancellation is confirmed.

### Financial reports

Support:
- Daily spending summaries
- Weekly financial briefings
- Monthly financial reports
- Subscription spending reports
- Budget comparisons
- Unusual transaction alerts

Financial summaries must be grounded in actual recorded transactions.

## 7. Phase 5 — Online Shopping and Agentic Payments

Build a secure shopping and payment execution workflow.

This is the most sensitive part of the project.

### Shopping Assistant

Capabilities:
- Understand shopping requests.
- Search for products.
- Compare merchants.
- Compare prices.
- Check shipping costs.
- Review return policies.
- Prepare shopping carts.
- Navigate supported official checkout flows.
- Present final purchase details.
- Request approval before payment.
- Record completed purchases and receipts.

### Digital subscriptions

Support services such as YouTube Premium where official billing flows and available payment methods permit automation.

The assistant should:
- Check the existing subscription status.
- Determine whether payment is due.
- Identify the billing provider.
- Verify the plan and price.
- Prepare the official checkout or renewal process.
- Request explicit approval.
- Execute only if the payment method and platform support it.
- Confirm the result using reliable payment evidence.

Do not bypass OTP, CAPTCHA, platform authentication, or other security mechanisms.

### Mandatory payment approval

Every transaction requires explicit, transaction-specific approval.

The approval request must include:
- Merchant
- Product or service
- Final amount
- Currency
- Shipping or additional fees
- Payment method identifier
- Recurring billing terms, where applicable
- Unique transaction identifier
- Approval expiry

Use a secure authenticated approval mechanism separate from ordinary chat text.

A generic "yes" must never authorize an unrelated or modified payment.

### Payment execution architecture

Implement a separate payment execution service.

Hermes may prepare purchase requests but must not directly access unrestricted payment credentials.

The payment service must independently verify:
- User authentication
- Approval status
- Transaction identity
- Amount and currency
- Merchant
- Expiration
- Duplicate execution attempts
- Payment method permissions

Use idempotency keys, audit logs, and explicit transaction states.

Never store raw card numbers, CVVs, banking passwords, or recovery phrases in prompts, model memory, or application logs.

### Critical restriction

**Do not enable real payment execution during Phases 1–4.**

During Phase 5:
1. Build a simulated payment environment.
2. Test the complete approval lifecycle.
3. Test declined, expired, changed, and duplicate requests.
4. Review security controls.
5. Enable supported live payments only after explicit authorization.

## 8. Persistent Data Architecture

Use SQLite as the primary structured database.

Organize the schema around:

- User profile
- Preferences
- Tasks
- Commitments
- Scheduled activities
- Conversation references
- Reading materials
- Reading progress
- Highlights
- Bible study notes
- Financial accounts
- Transactions
- Ledger entries
- Receipts
- Subscriptions
- Subscription charges
- Purchase requests
- Payment approvals
- Payment attempts
- Audit logs

Use database migrations, foreign keys, indexes, and transaction boundaries.

Enable WAL mode and configure regular backups.

Keep sensitive financial data logically separate from general memory.

## 9. Security Requirements

Implement security from the beginning, not as a final phase.

Requirements:
- Authorized sender restrictions
- Secure OAuth token storage
- Least-privilege API scopes
- Secret management
- Encryption in transit
- Encryption for sensitive stored data and backups
- Audit logging
- Tool execution restrictions
- Prompt-injection defenses
- Financial approval isolation
- Payment idempotency
- Error handling
- Backup and recovery
- Configurable data retention
- Memory inspection and deletion
- Secure process supervision

Treat external emails, documents, websites, and merchant pages as untrusted inputs.

External content must never override system instructions or grant tool permissions.

## 10. Skills Architecture

Create modular skills following Hermes's actual supported conventions.

Proposed skills:

- `subscription-manager`
- `personal-bookkeeper`
- `shopping-assistant`
- `payment-approval`
- `reading-companion`
- `bible-study`
- `daily-briefing`
- `commitment-tracker`
- `email-assistant`
- `calendar-assistant`
- `github-assistant`
- `research-assistant`
- `personal-memory`

Each skill must include:
- Purpose
- Activation conditions
- Supported tasks
- Required integrations
- Tool permissions
- Input validation
- Error handling
- Security restrictions
- Example conversations
- Acceptance tests

Do not duplicate functionality already implemented in Hermes.

## 11. Deployment and Reliability

Deploy to a Linux VPS without relying on my personal MacBook.

Requirements:
- Official Hermes installation
- Photon gateway setup
- Environment configuration
- Process supervision
- Automatic restart
- Persistent storage
- Health monitoring
- Log rotation
- Backups
- Recovery documentation
- Minimal exposed network ports
- Deployment verification

Provide a complete README explaining installation, configuration, updates, troubleshooting, and recovery.

Keep the deployment inexpensive and avoid unnecessary managed infrastructure.

## 12. Implementation Workflow

Work incrementally, phase by phase.

Before coding:

1. Inspect the repository.
2. Read relevant official documentation.
3. Identify existing Hermes functionality.
4. Identify missing functionality.
5. Propose the smallest maintainable extension.
6. Document assumptions and limitations.
7. Create an implementation plan.

Then implement the phase.

For each phase:
- Create the necessary skills and services.
- Add tests.
- Run tests where possible.
- Validate integrations.
- Document configuration.
- Record completed and outstanding tasks.
- Do not claim untested features work.

Do not replace Hermes's architecture unnecessarily.

Avoid placeholder implementations, fake API responses, and mock integrations presented as production functionality.

Mocks are acceptable only in explicitly identified tests and simulations.

## 13. Required Deliverables

Produce:

1. Complete project architecture.
2. Hermes configuration.
3. `SOUL.md` and initial `USER.md`.
4. Photon integration configuration.
5. VPS deployment scripts.
6. Voice configuration.
7. Morning and evening briefing schedules.
8. SQLite schema and migrations.
9. Modular Hermes skills.
10. Productivity integrations.
11. Reading and Bible study workflows.
12. Subscription and bookkeeping services.
13. Shopping and payment approval architecture.
14. Security documentation.
15. Automated tests.
16. Installation and operations README.
17. Phase-by-phase implementation checklist.

## 14. Definition of Done

The project is complete when the assistant can:

- Communicate reliably through iMessage.
- Receive and understand voice messages.
- Optionally respond with audio.
- Remember relevant context.
- Manage tasks and reminders.
- Send daily briefings at 08:00 and 20:00 Africa/Lagos.
- Assist with email, calendar, GitHub, and research.
- Explain reading materials and track progress.
- Support contextual Bible study.
- Maintain accurate financial records.
- Track subscriptions and renewals.
- Prepare online purchases.
- Request secure approval for payments.
- Execute only supported, explicitly approved transactions.
- Reconcile successful payments and receipts.
- Recover from errors without duplicate financial actions.
- Protect personal data and credentials.

## 15. Start Here

**Begin with Phase 1 only.**

First inspect the Hermes Agent repository and documentation.

Then:
1. Report the current architecture and relevant built-in capabilities.
2. Identify what can be configured without writing custom code.
3. Create the Phase 1 implementation plan.
4. Implement Hermes identity, memory, model configuration, Photon, voice, and scheduled briefings.
5. Prepare the VPS deployment.
6. Add security controls and acceptance tests.
7. Document the setup and any manual configuration required.

Do not start Phases 2–5 until Phase 1 has been implemented and validated.

Keep the complete project scope available as the development roadmap.

**Build a reliable personal assistant first. Expand its capabilities without compromising security, privacy, or maintainability.**