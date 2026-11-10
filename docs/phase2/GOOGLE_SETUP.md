> Superseded: owner selected managed OAuth through Composio on 2026-11-10.
> The manual Google Cloud instructions below are retained only as an alternative;
> no custom Google OAuth client is needed for the selected Composio setup.

# Google setup for Bailey

Start with read-only Gmail and Calendar access. Draft replies can be prepared as
text; no sending, message modification or calendar changes are enabled yet.
The installed Hermes Google setup script requests broad Workspace write scopes,
so Bailey uses the official Google OAuth library with only gmail.readonly and
calendar.readonly, while retaining Hermes' native credential-file locations.

1. Create/select a project at https://console.cloud.google.com/projectselector2/home/dashboard.
2. Enable **Gmail API** and **Google Calendar API** at https://console.cloud.google.com/apis/library.
3. Configure **Google Auth Platform → Branding/Audience**. For a personal Gmail
   account choose External, keep Testing, and add your own account as a test user.
4. At https://console.cloud.google.com/auth/clients create an OAuth client with
   application type **Desktop app**, named Bailey. Download its JSON file.
5. Give Codex the local file path, not its contents. Codex will prepare the private
   authorization flow. Do not paste client secrets, refresh tokens or callback codes.

Testing-mode refresh tokens for restricted scopes can expire; this must be tested
and documented rather than assuming unattended access lasts indefinitely.

Official references:
- https://developers.google.com/workspace/gmail/api/quickstart/python
- https://developers.google.com/workspace/calendar/api/auth
