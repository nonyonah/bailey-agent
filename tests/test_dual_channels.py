"""Both native channels share one owner; credentials below are test fixtures."""
import json
from pathlib import Path
import tempfile
import unittest
from bailey.profile import initialize, read_env, validate
from bailey.upgrade_channel import migrate


class DualChannelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        initialize(self.home, "+2348012345678", stt="local")

    def credentials(self):
        path = self.home / ".env"
        path.write_text(path.read_text() +
            "PHOTON_PROJECT_ID=fixture-project\nPHOTON_PROJECT_SECRET=fixture-secret\n"
            "WHATSAPP_CLOUD_PHONE_NUMBER_ID=123456789012345\n"
            "WHATSAPP_CLOUD_ACCESS_TOKEN=fixture-token\n"
            "WHATSAPP_CLOUD_APP_SECRET=" + "a" * 32 + "\n"
            "WHATSAPP_CLOUD_VERIFY_TOKEN=" + "b" * 43 + "\n")
        (self.home / "auth.json").write_text("{}")
        (self.home / "auth.json").chmod(0o600)

    def test_enabling_whatsapp_keeps_photon_and_preserves_history(self):
        self.credentials()
        memory = (self.home / "memories/USER.md").read_text()
        migrate(self.home, "+2348012345678", enable_whatsapp=True)
        cfg = validate(self.home, require_credentials=True)
        self.assertTrue(cfg["platforms"]["photon"]["enabled"])
        self.assertTrue(cfg["platforms"]["whatsapp_cloud"]["enabled"])
        self.assertEqual(cfg["platform_toolsets"]["photon"], cfg["platform_toolsets"]["whatsapp_cloud"])
        self.assertEqual((self.home / "memories/USER.md").read_text(), memory)

    def test_incomplete_whatsapp_cannot_change_live_profile(self):
        before = {name: (self.home / name).read_bytes() for name in ("config.yaml", ".env")}
        with self.assertRaises(ValueError):
            migrate(self.home, "+2348012345678", enable_whatsapp=True)
        for name, value in before.items():
            self.assertEqual((self.home / name).read_bytes(), value)

    def test_enabled_whatsapp_is_preserved_and_both_owner_targets_change(self):
        self.credentials()
        migrate(self.home, "+2348012345678", enable_whatsapp=True)
        migrate(self.home, "+2348098765432")
        self.assertTrue(validate(self.home)["platforms"]["whatsapp_cloud"]["enabled"])
        env = read_env(self.home / ".env")
        self.assertEqual(env["PHOTON_ALLOWED_USERS"], "+2348098765432")
        self.assertEqual(env["WHATSAPP_CLOUD_ALLOWED_USERS"], "2348098765432")

    def test_second_channel_cannot_authorize_another_owner(self):
        p = self.home / ".env"
        p.write_text(p.read_text().replace("WHATSAPP_CLOUD_ALLOWED_USERS=2348012345678", "WHATSAPP_CLOUD_ALLOWED_USERS=15551234567"))
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_enabling_second_channel_cannot_disable_photon(self):
        p = self.home / "config.yaml"
        cfg = json.loads(p.read_text())
        cfg["platforms"]["photon"]["enabled"] = False
        p.write_text(json.dumps(cfg))
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_slack_addition_preserves_imessage_and_defers_whatsapp(self):
        self.credentials()
        path = self.home / ".env"
        path.write_text(path.read_text() + "SLACK_ALLOWED_USERS=U123456789\nSLACK_BOT_TOKEN=xoxb-fixture\nSLACK_APP_TOKEN=xapp-fixture\n")
        migrate(self.home, "+2348012345678", enable_whatsapp=False, enable_slack=True)
        cfg = validate(self.home, require_credentials=True)
        self.assertTrue(cfg["platforms"]["slack"]["enabled"])
        self.assertTrue(cfg["platforms"]["photon"]["enabled"])
        self.assertFalse(cfg["platforms"]["whatsapp_cloud"]["enabled"])
        path.write_text(path.read_text().replace("U123456789", "U123456789,U987654321"))
        with self.assertRaises(ValueError):
            validate(self.home, require_credentials=True)

    def test_missing_slack_credentials_leave_imessage_configuration_intact(self):
        before = (self.home / "config.yaml").read_bytes()
        with self.assertRaises(ValueError):
            migrate(self.home, "+2348012345678", enable_slack=True)
        self.assertEqual((self.home / "config.yaml").read_bytes(), before)

    def test_slack_manifest_only_subscribes_to_private_one_to_one_messages(self):
        manifest = json.loads((Path(__file__).parents[1] / "config/slack-manifest.json").read_text())
        self.assertEqual(manifest["settings"]["event_subscriptions"]["bot_events"], ["message.im"])
        scopes = manifest["oauth_config"]["scopes"]["bot"]
        self.assertFalse(set(scopes) & {"channels:history", "groups:history", "mpim:history", "search:read"})
