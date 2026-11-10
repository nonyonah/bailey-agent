# Slack alongside iMessage

Selected 2026-11-10. iMessage is primary; Slack is a verified manual fallback.
Both are connected and real replies are confirmed. WhatsApp is deferred and disabled.

Both adapters use the existing Hermes profile, model, native memory and session
search. Their conversation threads remain separate. Briefings are now on demand in either
chat: ask “What do I have today?”. Both legacy cron jobs are paused. Replies stay
in the requesting chat; no duplicate pushes or automatic cross-channel failover.

## Create the app once

1. Open https://api.slack.com/apps → **Create New App → From an app manifest**.
   Select your workspace. Paste the JSON in `config/slack-manifest.json`.
2. Create the app, then **OAuth & Permissions → Install to Workspace** and approve
   the listed permissions. Keep the **Bot User OAuth Token** (`xoxb-…`) private.
3. In **Basic Information → App-Level Tokens**, generate a token named `Bailey`
   with **connections:write**. Keep the resulting `xapp-…` token private.
4. In Slack, open your own profile → **More → Copy member ID**.
5. In the project terminal, run:

```bash
bash deploy/connect-slack.sh
```

Enter the member ID and both tokens there. Token inputs are hidden, never command
arguments. The helper checks bot authentication, an active human owner in the same
workspace and Socket Mode token access. It privately preserves the previous env,
adds the restricted Slack configuration and keeps Photon enabled. It does not
restart the gateway; tell the operator when saved so they can restart and test.

The manifest enables the app's Messages tab and Socket Mode. It subscribes only
to `message.im`; it does not request public/private channel history or group-DM
history. `files:read` and `files:write` support the requested attachments and audio.
`users:read` verifies the allowed owner. No user OAuth token is required.

## Operator verification

After the private helper succeeds, run the existing credential/tool policy check
and restart **the existing** `bailey-gateway.service`. Verify both Slack and Photon
connect, ask the owner to DM Bailey, and confirm a real AI reply in each channel.
Do not claim setup complete from a manifest, saved token or successful auth call.
Do not create another gateway/profile or enable access for all workspace members.

No inbound public port or webhook is needed. The free InstaBox still has idle
pauses/runtime caps: neither Slack nor iMessage guarantees wakeup of a paused VM.
Do not promise continuous availability.

## Current evidence

All 29 local and Linux tests pass. Installed-Hermes restricted-tool/credential
checks pass for the current iMessage profile. Official Hermes Slack dependencies
were installed through `hermes pm install --extra slack`. The service permits writes to the native Hermes state/lock directory while keeping
the remainder of the home read-only. Both adapters report connected. The owner
confirmed a real Slack briefing reply; native delivery records show delivered. Voice, backup, reboot and other Phase 1 checks remain open.
