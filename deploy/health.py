"""Check the native Photon sidecar without exposing secrets."""
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


def check(home=Path("/home/bailey/data")):
    subprocess.run(["systemctl", "is-active", "--quiet", "bailey-gateway.service"], check=True)
    record_path = home / "photon-sidecar.json"
    if record_path.is_symlink() or record_path.stat().st_mode & 0o077:
        raise ValueError("Insecure sidecar runtime record")
    record = json.loads(record_path.read_text())
    port = int(record["port"])
    if not 1 <= port <= 65535:
        raise ValueError("Invalid sidecar port")
    request = urllib.request.Request(f"http://127.0.0.1:{port}/healthz", data=b"{}",
        headers={"Content-Type": "application/json", "X-Hermes-Sidecar-Token": record["token"]})
    # Never honor proxy environment variables for this loopback request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=5) as response:
        health = json.load(response)
    if health.get("ok") is not True:
        raise ValueError("Photon sidecar is not ready")
    config = json.loads((home / "config.yaml").read_text())
    if config["platforms"].get("slack", {}).get("enabled"):
        state = json.loads((home / "gateway_state.json").read_text())
        if state.get("platforms", {}).get("slack", {}).get("state") != "connected":
            raise ValueError("Slack transport is not connected")
    if config["platforms"]["whatsapp_cloud"]["enabled"]:
        with opener.open("http://127.0.0.1:8090/health", timeout=5) as response:
            cloud = json.load(response)
        if (cloud.get("verify_token_configured") is not True or
                cloud.get("app_secret_configured") is not True):
            raise ValueError("Signed WhatsApp receiver is not ready")


if __name__ == "__main__":
    try:
        check()
    except Exception:
        print("Bailey health FAILED; inspect local gateway and configured receivers", file=sys.stderr)
        sys.exit(1)
    print("Bailey gateway and configured receivers respond; delivery requires live checks")
