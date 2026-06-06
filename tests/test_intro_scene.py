import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.intro_scene import IntroScene


class IntroSceneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_advance_page_returns_start_action_on_last_page(self):
        start_action = {"type": "start", "level": 0}
        scene = IntroScene(start_action=start_action)
        scene.page_index = len(scene.pages) - 1

        action = scene.advance_page()

        self.assertEqual(start_action, action)

    def test_right_key_advances_intro_page(self):
        scene = IntroScene(start_action={"type": "start", "level": 0})
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)

        action = scene.handle_events([event])

        self.assertIsNone(action)
        self.assertEqual(1, scene.page_index)


if __name__ == "__main__":
    unittest.main()
