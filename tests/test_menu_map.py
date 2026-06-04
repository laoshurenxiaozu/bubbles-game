import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

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


if __name__ == "__main__":
    unittest.main()
