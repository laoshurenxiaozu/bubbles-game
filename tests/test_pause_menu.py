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

    def test_pause_menu_uses_main_menu_option_instead_of_map(self):
        scene = LevelScene()

        labels = [label for label, _ in scene.pause_options()]
        actions = [action for _, action in scene.pause_options()]

        self.assertIn("Main Menu", labels)
        self.assertNotIn("Map", labels)
        self.assertIn("main_menu", actions)
        self.assertNotIn("map", actions)

    def test_pause_main_menu_option_returns_menu_action(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.pause_menu_index = 2
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
        main_menu_center = scene.pause_tab_rect(2).center
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=main_menu_center,
            button=1,
        )

        action = scene.handle_events([event])

        self.assertEqual({"type": "menu"}, action)


if __name__ == "__main__":
    unittest.main()
