"""Create a fresh Hermes home. JSON is a strict subset of supported YAML."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PHONE = re.compile(r"\+[1-9][0-9]{7,14}\Z")
TOOLS = {"memory", "session_search", "tts"}


def reviewed_config(phase=1):
    if phase not in {1, 2}:
        raise ValueError("Unsupported implementation phase")
    return json.loads((ROOT / "config" / ("hermes.json" if phase == 1 else "hermes-phase2.json")).read_text())


def profile_phase(home):
    profile = json.loads((home / "bailey-profile.json").read_text())
    phase = profile.get("phase")
    if type(phase) is not int or phase not in {1, 2} or profile != {"schema": 1, "phase": phase, "payments": "disabled"}:
        raise ValueError("Unsupported profile metadata")
    return phase

ENV_DEFAULTS = {
    "PHOTON_ALLOW_ALL_USERS": "false",
    "PHOTON_TELEMETRY": "false",
    # Photon only offers mention gating for groups. An impossible regex closes
    # that gate even when someone says Bailey/Hermes; direct messages still work.
    "PHOTON_REQUIRE_MENTION": "true",
    "PHOTON_MENTION_PATTERNS": '["(?!)"]',
    "PHOTON_REACTIONS": "false",
    "SLACK_ALLOW_ALL_USERS": "false",
    "SLACK_ALLOW_BOTS": "false",
    "WHATSAPP_CLOUD_ALLOW_ALL_USERS": "false",
    "WHATSAPP_CLOUD_DM_POLICY": "allowlist",
    "WHATSAPP_CLOUD_WEBHOOK_HOST": "0.0.0.0",
    "WHATSAPP_CLOUD_WEBHOOK_PORT": "8090",
    "WHATSAPP_CLOUD_WEBHOOK_PATH": "/whatsapp/webhook",
}


def validate_whatsapp_credentials(env):
    for key in ("WHATSAPP_CLOUD_PHONE_NUMBER_ID", "WHATSAPP_CLOUD_ACCESS_TOKEN",
                "WHATSAPP_CLOUD_APP_SECRET", "WHATSAPP_CLOUD_VERIFY_TOKEN"):
        if not env.get(key):
            raise ValueError(f"Complete private Meta setup; missing {key}")
    if not re.fullmatch(r"[0-9]{13,20}", env["WHATSAPP_CLOUD_PHONE_NUMBER_ID"]):
        raise ValueError("Meta Phone Number ID must be an ID, not the business phone number")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", env["WHATSAPP_CLOUD_APP_SECRET"]):
        raise ValueError("Invalid Meta app secret format")
    if len(env["WHATSAPP_CLOUD_VERIFY_TOKEN"]) < 32:
        raise ValueError("Webhook verify token must be at least 32 characters")


def validate_slack_credentials(env):
    if not re.fullmatch(r"[UW][A-Z0-9]{8,}", env.get("SLACK_ALLOWED_USERS", "")):
        raise ValueError("Exactly one Slack owner member ID is required")
    if not env.get("SLACK_BOT_TOKEN", "").startswith("xoxb-"):
        raise ValueError("Slack bot token is missing or invalid")
    if not env.get("SLACK_APP_TOKEN", "").startswith("xapp-"):
        raise ValueError("Slack Socket Mode app token is missing or invalid")



def read_env(path):
    """Read simple dotenv values without executing shell code or exposing secrets."""
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        key, sep, value = line.partition("=")
        if not sep or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key):
            raise ValueError("Unsupported dotenv syntax; use KEY=value lines")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key] = value
    return result


def private_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Never follow a symlink when writing secrets or policy.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(content)


def load_document(path):
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import hermes_yaml as yaml
        except ImportError:
            import yaml
        return yaml.safe_load(text)


def initialize(home, phone, stt="groq"):
    if home.is_symlink():
        raise ValueError("Hermes home must not be a symlink")
    if not PHONE.fullmatch(phone):
        raise ValueError("Owner number must be E.164")
    if stt not in {"groq", "local"}:
        raise ValueError("STT must be groq or local")
    # Existing Hermes credentials/profile are never overwritten or silently merged.
    if home.exists() and any(home.iterdir()):
        raise ValueError("Hermes home must be empty; preserve existing profiles first")
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    home.chmod(0o700)
    config = json.loads((ROOT / "config/hermes.json").read_text())
    config["stt"]["provider"] = stt
    if stt == "local":
        config["stt"]["local"] = {"model": "small"}
    private_write(home / "config.yaml", json.dumps(config, indent=2) + "\n")
    private_write(home / "bailey-initial-config.json", json.dumps(config, indent=2) + "\n")
    env = {**ENV_DEFAULTS, "PHOTON_ALLOWED_USERS": phone,
           "PHOTON_HOME_CHANNEL": phone,
           "WHATSAPP_CLOUD_ALLOWED_USERS": phone[1:],
           "WHATSAPP_CLOUD_HOME_CHANNEL": phone[1:]}
    private_write(home / ".env", "".join(f"{key}={value}\n" for key, value in env.items()))
    private_write(home / "SOUL.md", (ROOT / "config/identity/SOUL.md").read_text())
    for name in ("USER.md", "MEMORY.md"):
        private_write(home / "memories" / name, (ROOT / "config/identity" / name).read_text())
    shutil.copytree(ROOT / "config/skills", home / "skills")
    (home / "skills").chmod(0o700)
    for path in (home / "skills").rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)
    private_write(home / ".no-bundled-skills", "")
    private_write(home / "bailey-profile.json", json.dumps({"schema": 1, "phase": 1, "payments": "disabled"}) + "\n")


def validate(home, require_credentials=False):
    if home.is_symlink() or home.stat().st_mode & 0o077:
        raise ValueError("Hermes home must be private (0700), not a symlink")
    for name in ("config.yaml", ".env", "SOUL.md", "bailey-profile.json"):
        path = home / name
        if path.is_symlink() or path.stat().st_mode & 0o077:
            raise ValueError(f"Insecure permissions: {name}")
    cfg = load_document(home / "config.yaml")
    phase = profile_phase(home)
    expected = reviewed_config(phase)
    plugins = home / "plugins"
    if plugins.exists():
        allowed = {"bailey_productivity"} if phase == 2 else set()
        if plugins.is_symlink() or any(p.name not in allowed for p in plugins.iterdir()
                                     if not p.name.startswith(".") and p.name != "__pycache__"):
            raise ValueError("Unreviewed local plugin")
    if phase == 2:
        plugin = home / "plugins" / "bailey_productivity"
        if not plugin.is_symlink() or plugin.resolve(strict=True) != (ROOT / "plugins/bailey_productivity").resolve(strict=True):
            raise ValueError("Install the reviewed root-owned productivity plugin first")
    # WhatsApp is an explicitly reviewed optional second channel. Other policy
    # changes still fail the exact comparison; Photon must stay enabled.
    cloud_enabled = cfg.get("platforms", {}).get("whatsapp_cloud", {}).get("enabled")
    if type(cloud_enabled) is not bool:
        raise ValueError("WhatsApp enabled must be a boolean")
    expected["platforms"]["whatsapp_cloud"]["enabled"] = cloud_enabled
    slack_enabled = cfg.get("platforms", {}).get("slack", {}).get("enabled")
    if type(slack_enabled) is not bool:
        raise ValueError("Slack enabled must be a boolean")
    expected["platforms"]["slack"]["enabled"] = slack_enabled
    if cfg.get("stt") in ({"provider": "local", "language": "en", "local": {"model": "base"}},
                           {"provider": "local", "language": "en", "local": {"model": "small"}}):
        expected["stt"] = cfg["stt"]
    # Exact policy prevents accidental extra MCP servers/providers/tools or fallback defaults.
    if cfg != expected:
        raise ValueError("Profile differs from reviewed Phase 1 policy")
    env = read_env(home / ".env")
    permitted_env = set(ENV_DEFAULTS) | {
        "WHATSAPP_CLOUD_ALLOW_ALL_USERS", "WHATSAPP_CLOUD_DM_POLICY",
        "WHATSAPP_CLOUD_WEBHOOK_HOST", "WHATSAPP_CLOUD_WEBHOOK_PORT", "WHATSAPP_CLOUD_WEBHOOK_PATH",
        "WHATSAPP_CLOUD_ALLOWED_USERS", "WHATSAPP_CLOUD_HOME_CHANNEL",
        "WHATSAPP_CLOUD_PHONE_NUMBER_ID", "WHATSAPP_CLOUD_ACCESS_TOKEN",
        "WHATSAPP_CLOUD_APP_SECRET", "WHATSAPP_CLOUD_VERIFY_TOKEN",
        "WHATSAPP_CLOUD_APP_ID", "WHATSAPP_CLOUD_WABA_ID", "WHATSAPP_CLOUD_API_VERSION",
        "GROQ_API_KEY", "OPENROUTER_API_KEY",
        "SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_ALLOWED_USERS",
        # Native Photon settings; endpoint overrides remain forbidden.
        "PHOTON_ALLOWED_USERS", "PHOTON_HOME_CHANNEL", "PHOTON_HOME_CHANNEL_NAME",
        "PHOTON_PROJECT_ID", "PHOTON_PROJECT_SECRET", "PHOTON_ALLOW_ALL_USERS",
        "PHOTON_TELEMETRY", "PHOTON_REQUIRE_MENTION", "PHOTON_MENTION_PATTERNS",
        "PHOTON_REACTIONS",
        "PHOTON_SIDECAR_AUTOSTART", "PHOTON_SIDECAR_PORT", "PHOTON_MAX_INLINE_ATTACHMENT_BYTES",
    }
    if set(env) - permitted_env:
        raise ValueError("Unreviewed dotenv settings; keep only Phase 1 settings and credentials")
    phone = env.get("PHOTON_ALLOWED_USERS", "")
    if not PHONE.fullmatch(phone) or env.get("PHOTON_HOME_CHANNEL") != phone:
        raise ValueError("Exactly one owner number and identical delivery target are required")
    if (env.get("WHATSAPP_CLOUD_ALLOWED_USERS") != phone[1:] or
            env.get("WHATSAPP_CLOUD_HOME_CHANNEL") != phone[1:]):
        raise ValueError("WhatsApp must use the same single owner and delivery target")
    for key, value in ENV_DEFAULTS.items():
        if env.get(key) != value:
            raise ValueError(f"Unsafe/missing setting: {key}")
    if any(k.endswith("ALLOW_ALL_USERS") and v.lower() not in {"false", "0", ""} for k, v in env.items()):
        raise ValueError("Allow-all sender access is forbidden")
    if require_credentials:
        if slack_enabled:
            validate_slack_credentials(env)
        if cloud_enabled:
            validate_whatsapp_credentials(env)
        for key in ("PHOTON_PROJECT_ID", "PHOTON_PROJECT_SECRET"):
            if not env.get(key):
                raise ValueError(f"Complete native Photon setup; missing {key}")
        if cfg["stt"]["provider"] == "groq" and not env.get("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY missing; configure it privately or choose local STT")
        auth = home / "auth.json"
        if not auth.is_file() or auth.is_symlink() or auth.stat().st_mode & 0o077:
            raise ValueError("Missing/insecure auth.json; complete model authentication")
    return cfg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["init", "check"])
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--phone")
    parser.add_argument("--stt", choices=["groq", "local"], default="groq")
    parser.add_argument("--credentials", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "init":
            initialize(args.home, args.phone or "", args.stt)
        else:
            validate(args.home, args.credentials)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Profile check failed: {exc}\n")
    print("Bailey profile ready" if args.action == "init" else "Bailey profile policy verified")


if __name__ == "__main__":
    main()
