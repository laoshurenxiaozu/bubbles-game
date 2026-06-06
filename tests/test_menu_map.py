import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.save_manager import SaveManager
from scenes.menu_scene import MenuScene


class MenuMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_map_node_centers_match_level_tabs(self):
        scene = MenuScene()

        centers = scene.level_node_centers()

        self.assertEqual(len(scene.level_tabs), len(centers))

    def test_locked_map_node_click_does_not_start_level(self):
        scene = MenuScene()
        scene.mode = "levels"
        scene.latest_level_index = 0
        locked_node = scene.level_node_centers()[2]

        action = scene.handle_click(locked_node)

        self.assertIsNone(action)
        self.assertNotEqual(2, scene.level_selected)

    def test_main_menu_level_selection_entry_is_labeled_level_map(self):
        scene = MenuScene()
        labels = [label for label, _ in scene.main_tabs]

        self.assertIn("Level Map", labels)
        self.assertIn("Start Game", labels)

    def test_main_menu_progress_restart_entry_is_labeled_level_map(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 1})
        labels = [label for label, _ in scene.main_tabs]

        self.assertIn("Level Map", labels)
        self.assertNotIn("Restart", labels)

    def test_main_menu_start_game_starts_current_level_directly(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2})
        start_index = [action for _, action in scene.main_tabs].index("start_game")

        action = scene.activate_main_tab(start_index)

        self.assertEqual(
            {
                "type": "start",
                "level": 1,
                "slot_index": None,
                "save_data": scene.progress_data,
            },
            action,
        )

    def test_main_menu_uses_latest_save_as_continue_progress(self):
        save_manager = SaveManager(Path("unused_save_slots.json"))
        save_manager.data = {
            "last_slot": 1,
            "slots": [
                None,
                {
                    "name": "Reef Run",
                    "current_level_index": 2,
                    "unlocked_levels": 2,
                    "latest_level_name": "Tutorial 2",
                    "seed_total": 4,
                },
                None,
            ],
        }

        scene = MenuScene(save_manager=save_manager)
        continue_index = [action for _, action in scene.main_tabs].index("continue")

        action = scene.activate_main_tab(continue_index)

        self.assertIsNone(action)
        self.assertEqual("levels", scene.mode)
        self.assertEqual(1, scene.progress_data["slot_index"])
        self.assertEqual(2, scene.level_selected)

    def test_main_menu_level_map_opens_level_selection(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2})
        map_index = [action for _, action in scene.main_tabs].index("level_map")

        action = scene.activate_main_tab(map_index)

        self.assertIsNone(action)
        self.assertEqual("levels", scene.mode)
        self.assertEqual(1, scene.level_selected)
        self.assertEqual(2, scene.latest_level_index)

    def test_menu_bubbles_rise_from_seafloor_and_loop(self):
        scene = MenuScene()
        bubble = scene.bubbles[0]

        start = scene.bubble_position_at_time(bubble, 0.0)
        later = scene.bubble_position_at_time(bubble, 1.0)
        looped = scene.bubble_position_at_time(bubble, bubble["duration"])

        self.assertGreater(start[1], later[1])
        self.assertGreater(start[1], 500)
        self.assertLess(later[1], 500)
        self.assertEqual(start, looped)


if __name__ == "__main__":
    unittest.main()
