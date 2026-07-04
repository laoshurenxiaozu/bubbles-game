import tempfile
import unittest
from pathlib import Path

from core.save_manager import SaveManager


class SettingsPersistenceTest(unittest.TestCase):
    def test_settings_round_trip_across_manager_instances(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "save_slots.json"
            manager = SaveManager(save_path)

            manager.save_settings(
                {
                    "music_volume": 40,
                    "sfx_volume": 30,
                    "restart_hint_enabled": False,
                    "control_hints_enabled": False,
                }
            )
            restored = SaveManager(save_path)

            self.assertEqual(
                {
                    "music_volume": 40,
                    "sfx_volume": 30,
                    "restart_hint_enabled": False,
                    "control_hints_enabled": False,
                },
                restored.get_settings(),
            )

    def test_legacy_save_file_receives_default_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "save_slots.json"
            save_path.write_text(
                '{"last_slot": null, "slots": [null, null, null]}',
                encoding="utf-8",
            )

            manager = SaveManager(save_path)

            self.assertEqual(
                SaveManager.DEFAULT_SETTINGS,
                manager.get_settings(),
            )

    def test_invalid_settings_are_clamped_or_defaulted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(
                Path(tmpdir) / "save_slots.json"
            )

            manager.save_settings(
                {
                    "music_volume": 140,
                    "sfx_volume": -5,
                    "restart_hint_enabled": "no",
                    "control_hints_enabled": "no",
                }
            )

            self.assertEqual(
                {
                    "music_volume": 100,
                    "sfx_volume": 0,
                    "restart_hint_enabled": True,
                    "control_hints_enabled": True,
                },
                manager.get_settings(),
            )


if __name__ == "__main__":
    unittest.main()
