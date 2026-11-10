"""Apply the reviewed messaging profile while preserving credentials and memory."""
import argparse
import json
from pathlib import Path
import os
import tempfile
from datetime import datetime, timezone
from bailey.profile import ENV_DEFAULTS, PHONE, ROOT, read_env, validate_whatsapp_credentials, validate_slack_credentials, profile_phase, reviewed_config


def replace_private(path, text):
    if path.is_symlink():
        raise ValueError("Refusing a symlinked configuration file")
    fd, temporary = tempfile.mkstemp(prefix=".bailey-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def migrate(home, phone, enable_whatsapp=None, enable_slack=None, phase=None):
    if not PHONE.fullmatch(phone) or home.is_symlink() or home.stat().st_mode & 0o077:
        raise ValueError("Use an E.164 owner number and private Hermes home")
    env_path = home / ".env"
    if env_path.is_symlink() or env_path.stat().st_mode & 0o077:
        raise ValueError("Existing credentials must be private and not symlinked")
    env = read_env(env_path)
    # Preserve an already enabled second channel during later owner migrations.
    from bailey.profile import load_document
    existing = load_document(home / "config.yaml")
    if enable_whatsapp is None:
        enable_whatsapp = existing.get("platforms", {}).get("whatsapp_cloud", {}).get("enabled", False)
    if enable_whatsapp:
        # Fail before any policy writes if private setup is incomplete.
        validate_whatsapp_credentials(env)
    if enable_slack is None:
        enable_slack = existing.get("platforms", {}).get("slack", {}).get("enabled", False)
    if enable_slack:
        validate_slack_credentials(env)
    for value in env.values():
        if any(c in value for c in "\r\n") or "'" in value:
            raise ValueError("Unsupported credential quoting; use native configuration privately")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = home / "bailey-profile-history" / stamp
    archive.mkdir(parents=True, mode=0o700)
    archive.parent.chmod(0o700)
    for name in ("config.yaml", ".env", "bailey-initial-config.json"):
        source = home / name
        if source.is_file():
            if source.is_symlink():
                raise ValueError("Refusing a symlinked profile")
            replace_private(archive / name, source.read_text())
    phase = profile_phase(home) if phase is None else phase
    config = reviewed_config(phase)
    config["platforms"]["whatsapp_cloud"]["enabled"] = enable_whatsapp
    config["platforms"]["slack"]["enabled"] = enable_slack
    # Local Whisper keeps transcription independent of another hosted API key.
    config["stt"] = {"provider": "local", "language": "en", "local": {"model": "small"}}
    env.update(ENV_DEFAULTS)
    env["PHOTON_ALLOWED_USERS"] = phone
    env["PHOTON_HOME_CHANNEL"] = phone
    env["WHATSAPP_CLOUD_ALLOWED_USERS"] = phone[1:]
    env["WHATSAPP_CLOUD_HOME_CHANNEL"] = phone[1:]
    env["PHOTON_ALLOW_ALL_USERS"] = "false"
    replace_private(home / "config.yaml", json.dumps(config, indent=2) + "\n")
    replace_private(home / "bailey-initial-config.json", json.dumps(config, indent=2) + "\n")
    replace_private(env_path, "".join(f"{key}='{value}'\n" for key, value in env.items()))
    replace_private(home / "bailey-profile.json", json.dumps({"schema": 1, "phase": phase, "payments": "disabled"}) + "\n")
    # auth.json, credential pool, session history and native memories are untouched.


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--phone", help="Defaults to the existing private Photon owner number")
    parser.add_argument("--enable-whatsapp", action="store_const", const=True, default=None)
    args = parser.parse_args()
    phone = args.phone or read_env(args.home / ".env").get("PHOTON_ALLOWED_USERS", "")
    migrate(args.home, phone, args.enable_whatsapp)
    print("Reviewed messaging profile applied; credentials/history preserved; gateway not restarted")
