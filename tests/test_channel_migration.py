"""Credential-like values here are explicit test fixtures, not integrations."""
from pathlib import Path
import tempfile
import unittest
from bailey.profile import initialize, read_env, validate
from bailey.upgrade_channel import migrate


class MigrationTests(unittest.TestCase):
    def test_preserves_credentials_and_history_and_disables_other_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            initialize(home, "+2348012345678")
            env = home / ".env"
            env.write_text(env.read_text() + "PHOTON_PROJECT_SECRET=test-fixture-secret\n")
            memory = home / "memories/USER.md"
            memory.write_text("Confirmed preference fixture\n")
            auth = home / "auth.json"
            auth.write_text('{"fixture": true}')
            migrate(home, "+2348098765432")
            cfg = validate(home)
            self.assertTrue(cfg["platforms"]["photon"]["enabled"])
            self.assertFalse(cfg["platforms"]["whatsapp_cloud"]["enabled"])
            self.assertFalse(cfg["platforms"]["telegram"]["enabled"])
            self.assertEqual(read_env(env)["PHOTON_PROJECT_SECRET"], "test-fixture-secret")
            self.assertEqual(read_env(env)["PHOTON_HOME_CHANNEL"], "+2348098765432")
            self.assertEqual(read_env(env)["PHOTON_ALLOWED_USERS"], "+2348098765432")
            self.assertEqual(memory.read_text(), "Confirmed preference fixture\n")
            self.assertEqual(auth.read_text(), '{"fixture": true}')
            self.assertTrue(list((home / "bailey-profile-history").glob("*/.env")))

    def test_rejects_symlinked_credentials_without_writing_elsewhere(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            initialize(home, "+2348012345678")
            env = home / ".env"
            target = home / "old-env"
            original = env.read_text()
            env.rename(target)
            env.symlink_to(target)
            with self.assertRaises(ValueError):
                migrate(home, "+2348012345678")
            self.assertEqual(target.read_text(), original)
