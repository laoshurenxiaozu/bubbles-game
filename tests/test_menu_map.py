import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.save_manager import SaveManager
from entities.player import Player
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

    def test_main_menu_shows_start_and_load_entries(self):
        scene = MenuScene()
        labels = [label for label, _ in scene.main_tabs]

        self.assertIn("Start a New Game", labels)
        self.assertIn("Load Game", labels)

    def test_main_menu_with_progress_shows_continue_without_restart_entry(self):
        scene = MenuScene(session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True})
        labels = [label for label, _ in scene.main_tabs]

        self.assertIn("Continue", labels)
        self.assertNotIn("Restart", labels)

    def test_main_menu_start_game_opens_intro_then_level_selection(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2})
        start_index = [action for _, action in scene.main_tabs].index("start_game")

        action = scene.activate_main_tab(start_index)

        self.assertEqual(
            {
                "type": "intro",
                "start_action": {
                    "type": "menu",
                    "progress_data": {
                        **scene.default_progress_data(),
                        "has_started_game": True,
                        "open_mode": "levels",
                    },
                },
            },
            action,
        )

    def test_menu_settings_toggles_restart_hint_in_progress(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True})
        scene.mode = "settings"
        scene.settings_index = 1

        scene.handle_key(pygame.K_RETURN)

        self.assertFalse(scene.restart_hint_enabled)
        self.assertFalse(scene.progress_data["restart_hint_enabled"])
        self.assertTrue(scene.session_dirty)

    def test_main_menu_with_saved_slots_still_uses_load_game_not_continue(self):
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
        labels = [label for label, _ in scene.main_tabs]

        self.assertNotIn("Continue", labels)
        self.assertIn("Load Game", labels)

    def test_continue_uses_runtime_session_progress(self):
        runtime_progress = {
            "current_level_index": 2,
            "unlocked_levels": 2,
            "has_started_game": True,
            "player_bubbles": 1,
            "player_seeds": 0,
            "seed_total": 0,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
        }
        scene = MenuScene(session_progress=runtime_progress)
        continue_index = [action for _, action in scene.main_tabs].index("continue")

        action = scene.activate_main_tab(continue_index)

        self.assertEqual("menu", action["type"])
        self.assertEqual("levels", action["progress_data"]["open_mode"])
        self.assertEqual(2, action["progress_data"]["current_level_index"])

    def test_level_map_save_button_opens_save_overlay(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2, "slot_index": 0})
        scene.mode = "levels"

        action = scene.handle_click(scene.level_save_rect().center)

        self.assertIsNone(action)
        self.assertEqual("level_save", scene.mode)

    def test_level_map_s_key_opens_save_overlay(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2, "slot_index": 0})
        scene.mode = "levels"

        action = scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, scancode=22)])

        self.assertIsNone(action)
        self.assertEqual("level_save", scene.mode)

    def test_level_map_down_arrow_does_not_open_save_overlay(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2, "slot_index": 0})
        scene.mode = "levels"

        action = scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)])

        self.assertIsNone(action)
        self.assertEqual("levels", scene.mode)

    def test_level_map_save_slot_double_click_starts_name_edit(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2, "slot_index": None})
        scene.mode = "levels"
        scene.begin_level_save()
        slot_center = scene.level_save_slot_rect(0).center

        scene.handle_click(slot_center)
        action = scene.handle_click(slot_center)

        self.assertIsNone(action)
        self.assertTrue(scene.save_editing)

    def test_level_map_right_key_moves_selected_level(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2})
        scene.mode = "levels"

        scene.handle_key(pygame.K_RIGHT)

        self.assertEqual(2, scene.level_selected)

    def test_level_map_save_click_uses_overlay_screen_coordinates(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2, "slot_index": 0})
        scene.mode = "levels"
        scene.begin_level_save()
        scene.save_flow = "choose_action"
        scene.save_action_index = 0

        action = scene.handle_click(scene.level_save_action_rect(1).center)

        self.assertIsNone(action)
        self.assertEqual("choose_slot", scene.save_flow)

    def test_load_game_prompts_before_overwriting_unsaved_session_progress(self):
        save_manager = SaveManager(Path("unused_save_slots.json"))
        save_manager.data = {
            "last_slot": 0,
            "slots": [
                {
                    "name": "Slot 1",
                    "current_level_index": 1,
                    "unlocked_levels": 1,
                    "latest_level_name": "Tutorial 1",
                    "seed_total": 1,
                },
                None,
                None,
            ],
        }
        scene = MenuScene(
            save_manager=save_manager,
            session_progress={"current_level_index": 0, "unlocked_levels": 0, "has_started_game": True},
            session_dirty=True,
        )
        scene.mode = "load"

        action = scene.activate_load_slot(0)

        self.assertIsNone(action)
        self.assertEqual("confirm", scene.mode)

    def test_unsaved_confirmation_save_button_opens_save_flow(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        action = scene.handle_click(scene.confirm_yes_rect().center)

        self.assertIsNone(action)
        self.assertEqual("level_save", scene.mode)
        self.assertEqual("confirm", scene.level_save_return_mode)
        self.assertTrue(scene.level_save_continue_after_save)

    def test_saving_from_unsaved_confirmation_continues_pending_action(self):
        progress = {
            "current_level_index": 1,
            "unlocked_levels": 1,
            "has_started_game": True,
            "player_bubbles": 1,
            "player_seeds": 2,
            "seed_total": 2,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            save_manager = SaveManager(Path(tmpdir) / "save_slots.json")
            scene = MenuScene(
                save_manager=save_manager,
                session_progress=progress,
                session_dirty=True,
            )
            scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)
            scene.begin_confirmation_save()
            scene.save_name_input = "Checkpoint"

            self.assertTrue(scene.save_to_slot(0))
            action = scene.close_level_save(show_message=True, saved=True)

            self.assertEqual({"type": "quit"}, action)
            self.assertFalse(scene.session_dirty)
            self.assertEqual(0, save_manager.get_slot(0)["slot_index"])

    def test_save_snapshot_preserves_restart_hint_setting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_manager = SaveManager(Path(tmpdir) / "save_slots.json")
            scene = MenuScene(
                save_manager=save_manager,
                progress_data={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            )
            scene.restart_hint_enabled = False
            scene.save_name_input = "Quiet Restart"

            self.assertTrue(scene.save_to_slot(0))

            self.assertFalse(save_manager.get_slot(0)["restart_hint_enabled"])

    def test_unsaved_confirmation_no_continues_without_saving(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        action = scene.handle_click(scene.confirm_no_rect().center)

        self.assertEqual({"type": "quit"}, action)

    def test_unsaved_confirmation_arrow_keys_switch_yes_no_selection(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        scene.handle_key(pygame.K_RIGHT)
        self.assertEqual("no", scene.confirm_selected)

        scene.handle_key(pygame.K_LEFT)
        self.assertEqual("yes", scene.confirm_selected)

    def test_unsaved_confirmation_enter_uses_selected_no_choice(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)
        scene.confirm_selected = "no"

        action = scene.handle_key(pygame.K_RETURN)

        self.assertEqual({"type": "quit"}, action)

    def test_unsaved_confirmation_hover_updates_selection(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        scene.update_hover(scene.confirm_no_rect().center)

        self.assertEqual("no", scene.confirm_selected)

    def test_unsaved_confirmation_close_cancels(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        action = scene.handle_click(scene.confirm_close_rect().center)

        self.assertIsNone(action)
        self.assertEqual("main", scene.mode)
        self.assertIsNone(scene.confirm_action)

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

    def test_level_hover_panel_sits_near_hovered_map_item(self):
        scene = MenuScene(progress_data={"current_level_index": 3, "unlocked_levels": 3})
        scene.mode = "levels"

        first_center = scene.level_node_centers()[0]
        scene.update_hover(first_center)
        first_rect = scene.level_hover_panel_rect()

        self.assertGreater(first_rect.left, first_center[0])
        self.assertLess(first_rect.left, 300)

        gate_center = scene.region_gate_center()
        scene.update_hover(gate_center)
        gate_rect = scene.level_hover_panel_rect()

        self.assertLess(gate_rect.right, gate_center[0])
        self.assertGreater(gate_rect.right, 500)

    def test_unlocking_thorn_reef_marks_progress_dirty_before_quit(self):
        progress = {
            "slot_index": 0,
            "current_level_index": 3,
            "latest_level_index": 3,
            "unlocked_levels": 3,
            "player_bubbles": 5,
            "player_seeds": 4,
            "seed_total": 4,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
            "has_started_game": True,
        }
        scene = MenuScene(
            progress_data=progress,
            session_progress=progress,
            session_dirty=False,
        )
        scene.unlock_player = Player((120, 150))
        scene.unlock_player.bubble_count = 1
        scene.unlock_player.seed_count = 0

        scene.finish_region_unlock()
        action = scene.request_quit_action()

        self.assertIsNone(action)
        self.assertTrue(scene.session_dirty)
        self.assertEqual("confirm", scene.mode)


if __name__ == "__main__":
    unittest.main()
