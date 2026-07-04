import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.game import Game


class FakeSound:
    def __init__(self):
        self.sfx_volume = 80
        self.music_volume = 60
        self.music_started = []
        self.stop_count = 0

    def get_sfx_volume(self):
        return self.sfx_volume

    def set_sfx_volume(self, volume):
        self.sfx_volume = volume

    def get_music_volume(self):
        return self.music_volume

    def set_music_volume(self, volume):
        self.music_volume = volume

    def play_music(self, name):
        self.music_started.append(name)

    def stop_music(self):
        self.stop_count += 1


class FakeSaveManager:
    def __init__(self):
        self.saved_settings = []

    def save_settings(self, settings):
        self.saved_settings.append(dict(settings))


class GameAudioTest(unittest.TestCase):
    def make_game(self):
        game = Game.__new__(Game)
        game.sound = FakeSound()
        game.save_manager = FakeSaveManager()
        game.settings = {
            "music_volume": 60,
            "sfx_volume": 80,
            "restart_hint_enabled": True,
        }
        game.session_progress = None
        game.session_dirty = False
        game.scene = SimpleNamespace()
        game.running = True
        return game

    def test_sync_scene_volume_updates_music_and_sfx(self):
        game = self.make_game()
        game.scene = SimpleNamespace(sfx_volume=70, music_volume=40)

        game.sync_scene_volume()

        self.assertEqual(70, game.sound.sfx_volume)
        self.assertEqual(40, game.sound.music_volume)

    def test_quit_action_persists_changed_scene_settings(self):
        game = self.make_game()
        game.running = True
        game.scene = SimpleNamespace(
            sfx_volume=30,
            music_volume=40,
            restart_hint_enabled=False,
        )

        game.handle_action({"type": "quit"})

        self.assertEqual(
            [
                {
                    "music_volume": 40,
                    "sfx_volume": 30,
                    "restart_hint_enabled": False,
                }
            ],
            game.save_manager.saved_settings,
        )
        self.assertFalse(game.running)

    def test_start_action_plays_level_music_with_current_volume(self):
        game = self.make_game()

        with patch("core.game.LevelScene") as level_scene:
            game.handle_action({"type": "start", "level": 2, "save_data": {}})

        level_scene.assert_called_once()
        self.assertEqual(60, level_scene.call_args.kwargs["music_volume"])
        self.assertEqual(["level"], game.sound.music_started)

    def test_menu_action_stops_level_music(self):
        game = self.make_game()

        with patch("core.game.MenuScene"):
            game.handle_action({"type": "menu", "progress_data": {}})

        self.assertEqual(1, game.sound.stop_count)


if __name__ == "__main__":
    unittest.main()
