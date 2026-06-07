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

    def test_pause_menu_keeps_level_map_without_main_menu_option(self):
        scene = LevelScene()

        labels = [label for label, _ in scene.pause_options()]
        actions = [action for _, action in scene.pause_options()]

        self.assertIn("Level Map", labels)
        self.assertIn("level_map", actions)
        self.assertNotIn("Main Menu", labels)
        self.assertNotIn("main_menu", actions)

    def test_pause_level_map_option_returns_level_selection_action(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.pause_menu_index = 2
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

        action = scene.handle_events([event])

        self.assertEqual("menu", action["type"])
        self.assertEqual("levels", action["progress_data"]["open_mode"])

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
        settings_center = scene.pause_tab_rect(3).center
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=settings_center,
            button=1,
        )

        action = scene.handle_events([event])

        self.assertIsNone(action)
        self.assertEqual("settings", scene.pause_mode)

    def test_pause_settings_option_opens_settings_view(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.pause_menu_index = 3
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

        action = scene.handle_events([event])

        self.assertIsNone(action)
        self.assertEqual("settings", scene.pause_mode)

    def test_pause_settings_escape_returns_to_pause_menu(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.activate_pause_choice("settings")
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

        action = scene.handle_events([event])

        self.assertIsNone(action)
        self.assertEqual("main", scene.pause_mode)
        self.assertEqual("menu", scene.state)

    def test_pause_settings_back_button_returns_to_pause_menu(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.activate_pause_choice("settings")
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=scene.pause_back_rect().center,
            button=1,
        )

        action = scene.handle_events([event])

        self.assertIsNone(action)
        self.assertEqual("main", scene.pause_mode)

    def test_pause_settings_adjusts_music_volume(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.activate_pause_choice("settings")
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)

        scene.handle_events([event])

        self.assertEqual(70, scene.music_volume)

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

    def test_progress_data_after_level_clear_points_to_next_unlocked_level(self):
        scene = LevelScene()
        scene.spawn_player()

        scene.complete_level()
        progress_data = scene.build_progress_data()

        self.assertEqual(1, progress_data["current_level_index"])
        self.assertEqual(1, progress_data["unlocked_levels"])
        self.assertEqual(0, progress_data["latest_level_index"])

    def test_final_level_clear_queues_ending_scene(self):
        scene = LevelScene(level_index=4)
        scene.spawn_player()

        scene.complete_level()
        action = scene.consume_pending_action()

        self.assertEqual("ending", action["type"])

    def test_result_overlay_mouse_click_opens_save_flow(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.complete_level()
        scene.result_menu_index = 2

        action = scene.handle_events(
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=scene.result_option_rect(2).center, button=1)]
        )

        self.assertIsNone(action)
        self.assertEqual("save", scene.result_mode)


if __name__ == "__main__":
    unittest.main()
