import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.level_scene import LevelScene


class PauseMenuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_pause_menu_keeps_level_map_and_main_menu_options(self):
        scene = LevelScene()

        labels = [label for label, _ in scene.pause_options()]
        actions = [action for _, action in scene.pause_options()]

        self.assertIn("Level Map", labels)
        self.assertIn("Main Menu", labels)
        self.assertIn("level_map", actions)
        self.assertIn("main_menu", actions)

    def test_pause_level_map_option_returns_level_selection_action(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.pause_menu_index = 2
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

        action = scene.handle_events([event])

        self.assertEqual("menu", action["type"])
        self.assertEqual("levels", action["progress_data"]["open_mode"])

    def test_pause_main_menu_option_returns_menu_action(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.pause_menu_index = 3
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

        action = scene.handle_events([event])

        self.assertEqual({"type": "menu"}, action)

    def test_pause_menu_hover_highlights_option(self):
        scene = LevelScene()
        scene.open_pause_menu()
        restart_center = scene.pause_tab_rect(1).center
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=restart_center)

        scene.handle_events([event])

        self.assertEqual(1, scene.pause_menu_index)

    def test_pause_menu_click_activates_option(self):
        scene = LevelScene()
        scene.open_pause_menu()
        main_menu_center = scene.pause_tab_rect(3).center
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=main_menu_center,
            button=1,
        )

        action = scene.handle_events([event])

        self.assertEqual({"type": "menu"}, action)

    def test_pause_menu_bubbles_rise_from_seafloor_and_loop(self):
        scene = LevelScene()
        bubble = scene.menu_bubbles[0]

        start = scene.menu_bubble_position_at_time(bubble, 0.0)
        later = scene.menu_bubble_position_at_time(bubble, 1.0)
        looped = scene.menu_bubble_position_at_time(bubble, bubble["duration"])

        self.assertGreater(start[1], later[1])
        self.assertGreater(start[1], 500)
        self.assertLess(later[1], 500)
        self.assertEqual(start, looped)


if __name__ == "__main__":
    unittest.main()
