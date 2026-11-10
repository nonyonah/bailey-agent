"""Private terminal onboarding for the existing native Slack adapter."""
import getpass
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request
from bailey.profile import read_env, validate_slack_credentials
from bailey.upgrade_channel import migrate, replace_private


def slack_call(method, token, **fields):
    request = urllib.request.Request(
        "https://slack.com/api/" + method,
        data=urllib.parse.urlencode(fields).encode(),
        headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise ValueError("Slack rejected the credentials or required permissions; check the app configuration")
    return result


def main():
    if not sys.stdin.isatty():
        raise ValueError("Run this setup in your private interactive terminal")
    home = Path(os.environ["HERMES_HOME"])
    env_path = home / ".env"
    if home.is_symlink() or env_path.is_symlink() or env_path.stat().st_mode & 0o077:
        raise ValueError("Existing profile credentials must be private")
    env = read_env(env_path)
    print("Bailey: add Slack alongside iMessage. Tokens stay private.")
    env["SLACK_ALLOWED_USERS"] = input("Your Slack member ID (profile → More → Copy member ID): ").strip()
    env["SLACK_BOT_TOKEN"] = getpass.getpass("Bot User OAuth Token (xoxb-…, hidden): ").strip()
    env["SLACK_APP_TOKEN"] = getpass.getpass("App-level Socket Mode token (xapp-…, hidden): ").strip()
    validate_slack_credentials(env)
    for value in env.values():
        if any(c in value for c in "\r\n'"):
            raise ValueError("Unsupported credential quoting")
    identity = slack_call("auth.test", env["SLACK_BOT_TOKEN"])
    owner = slack_call("users.info", env["SLACK_BOT_TOKEN"], user=env["SLACK_ALLOWED_USERS"]).get("user", {})
    if (owner.get("id") != env["SLACK_ALLOWED_USERS"] or owner.get("is_bot") or
            owner.get("deleted") or owner.get("team_id") != identity.get("team_id")):
        raise ValueError("Slack owner must be an active human member of the bot's workspace")
    slack_call("apps.connections.open", env["SLACK_APP_TOKEN"])
    env["SLACK_ALLOW_ALL_USERS"] = "false"
    env["SLACK_ALLOW_BOTS"] = "false"
    # Migration creates the profile archive. Preserve the pre-onboarding env too.
    private_backup = home / "bailey-before-slack.env"
    if not private_backup.exists():
        replace_private(private_backup, env_path.read_text())
    replace_private(env_path, "".join(f"{key}='{value}'\n" for key, value in env.items()))
    migrate(home, env["PHOTON_ALLOWED_USERS"], enable_whatsapp=False, enable_slack=True)
    print("Slack credentials verified and saved; iMessage preserved. Gateway restart is pending.")


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt):
        print("Slack setup incomplete. Check the private app settings and retry; no credentials are printed.", file=sys.stderr)
        sys.exit(1)
