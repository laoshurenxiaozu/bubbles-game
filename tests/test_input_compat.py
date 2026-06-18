import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.intro_scene import IntroScene
from scenes.menu_scene import MenuScene


class InputCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_menu_accepts_physical_scancode_for_down_navigation(self):
        scene = MenuScene()
        start_selected = scene.selected

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, scancode=22)])

        self.assertEqual((start_selected + 1) % len(scene.main_tabs), scene.selected)

    def test_menu_accepts_physical_scancode_for_yes_no_confirmation(self):
        scene = MenuScene(session_progress={"has_started_game": True}, session_dirty=True)
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        action = scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, scancode=17)])

        self.assertEqual({"type": "quit"}, action)

    def test_intro_accepts_physical_scancode_for_page_navigation(self):
        scene = IntroScene(start_action={"type": "start", "level": 0})

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, scancode=7)])

        self.assertEqual(1, scene.page_index)


if __name__ == "__main__":
    unittest.main()
