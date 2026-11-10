from pathlib import Path
import tempfile
import unittest
from bailey.profile import ROOT, initialize, validate
from bailey.upgrade_channel import migrate


class Phase2ProfileTests(unittest.TestCase):
    def test_reviewed_plugin_is_required_before_phase2_can_start(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)/'home'
            initialize(home,'+2348012345678',stt='local')
            migrate(home,'+2348012345678',phase=2)
            with self.assertRaises(ValueError):
                validate(home)
            (home/'plugins').mkdir(mode=0o700)
            (home/'plugins/bailey_productivity').symlink_to(ROOT/'plugins/bailey_productivity',target_is_directory=True)
            config = validate(home)
            self.assertIn('bailey_tasks',config['platform_toolsets']['slack'])
            self.assertIn('terminal',config['agent']['disabled_toolsets'])

    def test_later_channel_migration_preserves_phase2_task_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)/'home'
            initialize(home,'+2348012345678',stt='local')
            (home/'plugins').mkdir(mode=0o700)
            (home/'plugins/bailey_productivity').symlink_to(ROOT/'plugins/bailey_productivity',target_is_directory=True)
            migrate(home,'+2348012345678',phase=2)
            migrate(home,'+2348098765432')
            self.assertIn('bailey_tasks',validate(home)['platform_toolsets']['photon'])
