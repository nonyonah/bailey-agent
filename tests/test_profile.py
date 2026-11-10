import json
from pathlib import Path
import tempfile
import unittest

from bailey.profile import initialize, validate


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "hermes"
        initialize(self.home, "+2348012345678")

    def test_private_profile_and_native_locations(self):
        cfg = validate(self.home)
        self.assertEqual(cfg["timezone"], "Africa/Lagos")
        self.assertTrue((self.home / "memories/USER.md").is_file())
        self.assertTrue((self.home / "SOUL.md").is_file())
        self.assertEqual((self.home / ".env").stat().st_mode & 0o777, 0o600)

    def test_refuse_overwriting_memories_or_credentials(self):
        with self.assertRaises(ValueError):
            initialize(self.home, "+2348012345678")

    def test_reject_phone_lists_wildcards_and_shell_input(self):
        for phone in ("", "*", "2348012345678", "+2348012345678,+15551234567", "$(whoami)"):
            with self.subTest(phone=phone), self.assertRaises(ValueError):
                initialize(Path(self.tmp.name) / "other", phone)

    def test_fail_closed_if_owner_or_delivery_target_changes(self):
        env = self.home / ".env"
        env.write_text(env.read_text().replace("PHOTON_HOME_CHANNEL=+2348012345678", "PHOTON_HOME_CHANNEL=+15551234567"))
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_allow_all_cannot_override_owner_restriction(self):
        env = self.home / ".env"
        env.write_text(env.read_text().replace("PHOTON_ALLOW_ALL_USERS=false", "PHOTON_ALLOW_ALL_USERS=true"))
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_extra_connectors_or_browser_tools_rejected(self):
        for key, value in (("mcp_servers", {"payments": {"command": "pay"}}),
                           ("platform_toolsets", {"photon": ["browser", "terminal"]})):
            with self.subTest(key=key):
                path = self.home / "config.yaml"
                original = path.read_text()
                config = json.loads(original)
                config[key] = value
                path.write_text(json.dumps(config))
                with self.assertRaises(ValueError):
                    validate(self.home)
                path.write_text(original)

    def test_unreviewed_endpoint_override_rejected(self):
        env = self.home / ".env"
        env.write_text(env.read_text() + "PHOTON_SPECTRUM_HOST=https://attacker.invalid\n")
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_missing_credentials_block_live_start(self):
        with self.assertRaises(ValueError):
            validate(self.home, require_credentials=True)

    def test_group_gate_cannot_be_relaxed_by_profile_edit(self):
        env = self.home / ".env"
        env.write_text(env.read_text().replace("PHOTON_REQUIRE_MENTION=true", "PHOTON_REQUIRE_MENTION=false"))
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_public_secrets_rejected(self):
        (self.home / ".env").chmod(0o644)
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_symlinked_secrets_rejected(self):
        env = self.home / ".env"
        other = self.home / "other"
        env.rename(other)
        env.symlink_to(other)
        with self.assertRaises(ValueError):
            validate(self.home)

    def test_local_stt_is_an_explicit_alternative(self):
        other = Path(self.tmp.name) / "local"
        initialize(other, "+2348012345678", stt="local")
        self.assertEqual(validate(other)["stt"]["provider"], "local")
