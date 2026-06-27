import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from levels.catalog import level_count
from scenes.level_scene import EMPTY_BUBBLE_RESTART_HINT, LevelScene
from scenes.level_scene import RESTART_HINT_TEXTS


class RecordingSound:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


class PauseMenuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_pause_menu_uses_exit_label_for_level_map_action(self):
        scene = LevelScene()

        labels = [label for label, _ in scene.pause_options()]
        actions = [action for _, action in scene.pause_options()]

        self.assertIn("退出", labels)
        self.assertIn("level_map", actions)
        self.assertNotIn("关卡地图", labels)
        self.assertNotIn("主菜单", labels)
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

    def test_pause_settings_adjusts_sfx_volume_separately(self):
        scene = LevelScene(sfx_volume=80)
        scene.open_pause_menu()
        scene.activate_pause_choice("settings")
        scene.pause_settings_index = 1
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)

        scene.handle_events([event])

        self.assertEqual(80, scene.music_volume)
        self.assertEqual(70, scene.sfx_volume)

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

    def test_level_draw_renders_leaf_art(self):
        scene = LevelScene()
        scene.intro_active = False
        screen = pygame.Surface((960, 540))

        scene.draw(screen)

        self.assertIsNone(scene.player)

    def test_progress_data_after_level_clear_points_to_next_unlocked_level(self):
        scene = LevelScene()
        scene.spawn_player()

        scene.complete_level()
        progress_data = scene.build_progress_data()

        self.assertEqual(1, progress_data["current_level_index"])
        self.assertEqual(1, progress_data["unlocked_levels"])
        self.assertEqual(0, progress_data["latest_level_index"])

    def test_result_restart_restores_progress_to_level_entry_snapshot(self):
        scene = LevelScene(
            level_index=0,
            save_data={
                "unlocked_levels": 0,
                "completed_level_states": {},
                "stars_by_level": {},
                "current_region": "nursery",
                "thorn_reef_unlocked": False,
                "latest_level_index": 0,
                "latest_level_name": "Tutorial1",
                "has_started_game": True,
                "restart_hint_enabled": False,
            },
        )
        scene.spawn_player()
        scene.player.seed_count = 2

        scene.complete_level()
        self.assertEqual(1, scene.unlocked_levels)
        self.assertIn(0, scene.completed_level_states)
        self.assertIn("0", scene.stars_by_level)

        scene.restart_current_level()

        self.assertEqual("playing", scene.state)
        self.assertEqual(0, scene.unlocked_levels)
        self.assertEqual({}, scene.completed_level_states)
        self.assertEqual({}, scene.stars_by_level)
        self.assertEqual(0, scene.latest_level_index)
        self.assertEqual("Tutorial1", scene.latest_level_name)
        self.assertEqual(0, scene.player_seeds)

    def test_goal_leaf_collision_ignores_empty_rect_corner(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.player.x = scene.goal.rect.left - 18
        scene.player.y = scene.goal.rect.top + 4

        scene.update(0)

        self.assertEqual("playing", scene.state)

    def test_goal_leaf_collision_completes_on_leaf_body(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.player.x = scene.goal.rect.centerx
        scene.player.y = scene.goal.rect.centery

        scene.update(0)

        self.assertEqual("results", scene.state)

    def test_keydown_events_drive_horizontal_movement(self):
        scene = LevelScene()
        scene.spawn_player()
        start_x = scene.player.x

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)])
        scene.update(0.1)
        right_x = scene.player.x
        scene.handle_events([pygame.event.Event(pygame.KEYUP, key=pygame.K_d)])

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)])
        scene.update(0.1)
        left_x = scene.player.x
        scene.handle_events([pygame.event.Event(pygame.KEYUP, key=pygame.K_LEFT)])

        self.assertGreater(right_x, start_x)
        self.assertLess(left_x, right_x)

    def test_physical_scancode_events_drive_horizontal_movement(self):
        scene = LevelScene()
        scene.spawn_player()
        start_x = scene.player.x

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, scancode=7)])
        scene.update(0.1)
        right_x = scene.player.x
        scene.handle_events([pygame.event.Event(pygame.KEYUP, key=0, scancode=7)])

        self.assertGreater(right_x, start_x)

    def test_level_start_only_accepts_d_or_right(self):
        for key in (pygame.K_RETURN, pygame.K_SPACE):
            scene = LevelScene()
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=key)])
            self.assertIsNone(scene.player)

        for key in (pygame.K_d, pygame.K_RIGHT):
            scene = LevelScene()
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=key)])
            self.assertIsNotNone(scene.player)

    def test_focus_loss_clears_direction_key_state(self):
        scene = LevelScene()

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, scancode=7)])
        self.assertTrue(scene.right_down)

        scene.handle_events([pygame.event.Event(pygame.WINDOWFOCUSLOST)])

        self.assertFalse(scene.left_down)
        self.assertFalse(scene.right_down)

    def test_result_summary_r_shortcut_restarts_level(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.player.seed_count = 2
        scene.complete_level()

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)])

        self.assertEqual("restart_hint", scene.state)
        self.assertIsNone(scene.player)

    def test_restart_hint_finishes_into_playing_state(self):
        scene = LevelScene()
        scene.spawn_player()

        scene.restart_current_level()
        scene.update(scene.restart_hint_duration + 0.4)

        self.assertEqual("playing", scene.state)
        self.assertIsNone(scene.player)

    def test_restart_hint_uses_random_prompt_text(self):
        scene = LevelScene()
        scene.spawn_player()
        prompt = RESTART_HINT_TEXTS[-1]

        with patch("scenes.level_scene.random.choice", return_value=prompt) as choice:
            scene.restart_current_level()

        choice.assert_called_once_with(RESTART_HINT_TEXTS)
        self.assertEqual(prompt, scene.restart_hint_text)

    def test_restart_after_empty_bubble_death_uses_fixed_prompt(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.player.bubble_count = 0
        scene.update(0)

        with patch("scenes.level_scene.random.choice") as choice:
            scene.restart_current_level()

        choice.assert_not_called()
        self.assertEqual("restart_hint", scene.state)
        self.assertEqual(EMPTY_BUBBLE_RESTART_HINT, scene.restart_hint_text)

    def test_restart_hint_any_key_skips_with_short_fade(self):
        scene = LevelScene()
        scene.spawn_player()

        scene.restart_current_level()
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        scene.update(0.21)

        self.assertEqual("playing", scene.state)
        self.assertIsNone(scene.player)

    def test_restart_hint_can_be_disabled(self):
        scene = LevelScene(save_data={"restart_hint_enabled": False})
        scene.spawn_player()

        scene.restart_current_level()

        self.assertEqual("playing", scene.state)
        self.assertIsNone(scene.player)

    def test_pause_settings_toggles_restart_hint(self):
        scene = LevelScene()
        scene.open_pause_menu()
        scene.activate_pause_choice("settings")
        scene.pause_settings_index = 2

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])

        self.assertFalse(scene.restart_hint_enabled)

    def test_lost_screen_m_shortcut_returns_level_map(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.state = "lost"

        action = scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)])

        self.assertEqual("menu", action["type"])
        self.assertEqual("levels", action["progress_data"]["open_mode"])

    def test_final_level_clear_queues_ending_scene(self):
        scene = LevelScene(level_index=level_count() - 1)
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

    def test_result_menu_hover_plays_move_sound_when_selection_changes(self):
        scene = LevelScene()
        scene.spawn_player()
        scene.complete_level()
        scene.sound = RecordingSound()

        scene.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=scene.result_option_rect(1).center)])

        self.assertIn("menu_move", scene.sound.played)

    def test_result_menu_uses_exit_label_for_level_map_action(self):
        scene = LevelScene()

        self.assertEqual("退出", scene.result_choice_label("level_map"))


if __name__ == "__main__":
    unittest.main()
