import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.save_manager import SaveManager
from entities.player import Player
from levels.catalog import (
    DEFAULT_REGION,
    THORN_REEF_REGION,
    first_level_index,
    last_level_index,
)
from scenes.level_scene import LevelScene
from scenes.menu_scene import MenuScene
from ui.region_unlock import UNLOCK_LORE_HINT


class RecordingSound:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


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

    def test_locked_level_uses_dormant_branch_message(self):
        scene = MenuScene(
            progress_data={
                "current_level_index": 0,
                "unlocked_levels": 0,
            }
        )
        scene.mode = "levels"

        action = scene.activate_level_node(1)

        self.assertIsNone(action)
        self.assertEqual(
            "新的枝芽，还未在这里绽放",
            scene.map_message,
        )

    def test_main_menu_shows_start_and_load_entries(self):
        scene = MenuScene()
        labels = [label for label, _ in scene.main_tabs]

        self.assertIn("开始新游戏", labels)
        self.assertIn("读取存档", labels)

    def test_main_menu_with_progress_shows_continue_without_restart_entry(self):
        scene = MenuScene(session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True})
        labels = [label for label, _ in scene.main_tabs]

        self.assertIn("继续游戏", labels)
        self.assertNotIn("重新开始", labels)

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
        scene.settings_index = 2

        scene.handle_key(pygame.K_RETURN)

        self.assertFalse(scene.restart_hint_enabled)
        self.assertFalse(scene.progress_data["restart_hint_enabled"])
        self.assertTrue(scene.session_dirty)

    def test_menu_settings_adjusts_sfx_volume_separately(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True}, sfx_volume=80)
        scene.mode = "settings"
        scene.settings_index = 1

        scene.handle_key(pygame.K_LEFT)

        self.assertEqual(80, scene.music_volume)
        self.assertEqual(70, scene.sfx_volume)

    def test_menu_settings_toggles_control_hints(self):
        scene = MenuScene()
        scene.mode = "settings"
        scene.settings_index = 3

        scene.handle_key(pygame.K_RETURN)

        self.assertFalse(scene.control_hints_enabled)

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

        self.assertNotIn("继续游戏", labels)
        self.assertIn("读取存档", labels)

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

    def test_level_map_old_button_areas_have_no_click_actions(self):
        scene = MenuScene(progress_data={"current_level_index": 1, "unlocked_levels": 2, "slot_index": 0})
        scene.mode = "levels"

        save_action = scene.handle_click((102, 59))
        back_action = scene.handle_click((868, 511))

        self.assertIsNone(save_action)
        self.assertIsNone(back_action)
        self.assertEqual("levels", scene.mode)

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

        self.assertEqual("no", scene.confirm_selected)

        scene.handle_key(pygame.K_RIGHT)
        self.assertEqual("yes", scene.confirm_selected)

        scene.handle_key(pygame.K_LEFT)
        self.assertEqual("no", scene.confirm_selected)

    def test_unsaved_confirmation_no_button_is_left_of_save_button(self):
        scene = MenuScene(
            session_progress={"current_level_index": 1, "unlocked_levels": 1, "has_started_game": True},
            session_dirty=True,
        )
        scene.begin_confirmation({"type": "quit"}, "Unsaved", allow_save=True)

        self.assertLess(scene.confirm_no_rect().centerx, scene.confirm_yes_rect().centerx)

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

    def test_level_map_hover_plays_move_sound_when_selection_changes(self):
        scene = MenuScene(progress_data={"current_level_index": 0, "unlocked_levels": 2})
        scene.mode = "levels"
        scene.sound = RecordingSound()

        scene.update_hover(scene.level_node_centers()[1])

        self.assertIn("menu_move", scene.sound.played)

    def test_level_preview_runs_real_world_without_player(self):
        scene = MenuScene(
            progress_data={
                "current_level_index": 1,
                "latest_level_index": 1,
                "unlocked_levels": 1,
            }
        )
        scene.mode = "levels"
        scene.level_selected = 1

        scene.update(0.1)

        preview = scene.level_preview_scene
        self.assertIsNone(preview.player)
        self.assertTrue(preview.preview_active)
        self.assertEqual(1, len(preview.free_bubbles))
        self.assertLess(preview.free_bubbles[0].y, 512)

    def test_level_preview_uses_completed_level_state_without_mutating_it(self):
        completed_state = {
            "wild_seeds": [],
            "free_bubbles": [
                {
                    "x": 432,
                    "y": 321,
                    "bubble_count": 1,
                    "seed_count": 0,
                }
            ],
            "dropped_seeds": [],
            "fusion_bubbles": [],
            "souvenirs": [],
            "pending_object_spawns": [],
        }
        progress = {
            "current_level_index": 0,
            "latest_level_index": 0,
            "unlocked_levels": 0,
            "completed_level_states": {"0": completed_state},
        }
        original = deepcopy(progress)
        scene = MenuScene(progress_data=progress)
        scene.mode = "levels"

        scene.update(0.0)

        preview = scene.level_preview_scene
        self.assertEqual(432, preview.free_bubbles[0].x)
        self.assertEqual(321, preview.free_bubbles[0].y)
        self.assertEqual(original, progress)

    def test_level_preview_pixels_come_directly_from_level_world(self):
        scene = MenuScene(
            progress_data={
                "current_level_index": 0,
                "latest_level_index": 0,
                "unlocked_levels": 0,
            }
        )
        scene.mode = "levels"
        scene.level_selected = 0
        scene.update(0.1)

        actual = pygame.Surface((192, 108))
        scene.draw_level_preview(
            actual,
            actual.get_rect(),
            0,
        )
        world = pygame.Surface((960, 540))
        scene.level_preview_scene.draw_world(world)
        expected = pygame.transform.smoothscale(
            world,
            actual.get_size(),
        )

        self.assertEqual(
            pygame.image.tostring(expected, "RGB"),
            pygame.image.tostring(actual, "RGB"),
        )

    def test_final_preview_keeps_level_pixels_opaque_inside_rounding(self):
        scene = MenuScene(
            progress_data={
                "current_level_index": 2,
                "latest_level_index": 3,
                "unlocked_levels": 3,
            }
        )
        scene.mode = "levels"
        scene.level_selected = 2
        scene.update(0.1)

        screen = pygame.Surface((960, 540))
        scene.draw(screen)
        preview_rect = scene.level_hover_panel_rect().inflate(-6, -6)
        expected = pygame.Surface(preview_rect.size)
        scene.draw_level_preview(
            expected,
            expected.get_rect(),
            2,
        )

        for y in range(7, preview_rect.height - 7):
            for x in range(7, preview_rect.width - 7):
                self.assertEqual(
                    expected.get_at((x, y))[:3],
                    screen.get_at(
                        (preview_rect.left + x, preview_rect.top + y)
                    )[:3],
                )

    def test_entering_level_preserves_d_start_logic(self):
        scene = MenuScene(
            progress_data={
                "current_level_index": 1,
                "latest_level_index": 1,
                "unlocked_levels": 1,
            }
        )
        scene.mode = "levels"
        scene.level_selected = 1
        scene.update(0.25)
        self.assertEqual(
            1,
            len(scene.level_preview_scene.free_bubbles),
        )

        action = scene.activate_level_node(1)
        playable = LevelScene(
            level_index=action["level"],
            save_data=action["save_data"],
        )

        self.assertIsNone(playable.player)
        self.assertEqual([], playable.free_bubbles)

        playable.handle_events(
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)]
        )
        playable.update(0.1)

        self.assertIsNotNone(playable.player)
        self.assertEqual(1, len(playable.free_bubbles))

    def test_level_preview_follows_selected_map_node(self):
        scene = MenuScene(progress_data={"current_level_index": 3, "unlocked_levels": 3})
        scene.mode = "levels"

        first_center = scene.level_node_centers()[0]
        scene.update_hover(first_center)
        first_rect = scene.level_hover_panel_rect()

        self.assertEqual(first_center[0], first_rect.centerx)
        self.assertLess(first_rect.bottom, first_center[1])

        last_center = scene.level_node_centers()[-1]
        scene.update_hover(last_center)
        last_rect = scene.level_hover_panel_rect()

        self.assertEqual(last_center[0], last_rect.centerx)
        self.assertLess(last_rect.bottom, last_center[1])

    def test_region_gate_is_selected_after_last_nursery_level_clear(self):
        nursery_end = last_level_index(DEFAULT_REGION)
        reef_start = first_level_index(THORN_REEF_REGION)
        scene = MenuScene(
            progress_data={
                "current_level_index": reef_start,
                "latest_level_index": nursery_end,
                "unlocked_levels": reef_start,
                "current_region": DEFAULT_REGION,
                "thorn_reef_unlocked": False,
            }
        )

        self.assertEqual("gate", scene.level_selected)

    def test_region_gate_is_hidden_until_every_level_is_unlocked(self):
        nursery_end = last_level_index(DEFAULT_REGION)
        scene = MenuScene(
            progress_data={
                "current_level_index": nursery_end - 1,
                "unlocked_levels": nursery_end - 1,
                "current_region": DEFAULT_REGION,
                "thorn_reef_unlocked": False,
            }
        )

        self.assertFalse(scene.show_region_gate())

        scene.latest_level_index = nursery_end

        self.assertTrue(scene.show_region_gate())

    def test_region_unlock_confirmation_has_lore_hint(self):
        self.assertEqual(
            "泡泡将承载生命种子，唤醒沉睡的海域",
            UNLOCK_LORE_HINT,
        )

    def test_final_gate_appears_after_sixth_level_clear(self):
        reef_end = last_level_index(THORN_REEF_REGION)
        scene = MenuScene(
            progress_data={
                "current_level_index": reef_end,
                "latest_level_index": reef_end,
                "unlocked_levels": reef_end + 1,
                "current_region": THORN_REEF_REGION,
                "viewed_region": THORN_REEF_REGION,
                "thorn_reef_unlocked": True,
                "final_gate_completed": False,
            }
        )

        self.assertTrue(scene.show_region_gate())
        self.assertEqual("gate", scene.level_selected)
        self.assertEqual(5, scene.unlock_seed_cost)
        self.assertEqual("最终检测", scene.unlock_gate_label())

    def test_final_gate_stays_hidden_before_sixth_level_clear(self):
        reef_end = last_level_index(THORN_REEF_REGION)
        scene = MenuScene(
            progress_data={
                "current_level_index": reef_end,
                "unlocked_levels": reef_end,
                "current_region": THORN_REEF_REGION,
                "viewed_region": THORN_REEF_REGION,
                "thorn_reef_unlocked": True,
            }
        )

        self.assertFalse(scene.show_region_gate())

    def test_final_unlock_queues_ending_scene(self):
        reef_end = last_level_index(THORN_REEF_REGION)
        scene = MenuScene(
            progress_data={
                "current_level_index": reef_end,
                "latest_level_index": reef_end,
                "unlocked_levels": reef_end + 1,
                "player_bubbles": 6,
                "player_seeds": 5,
                "current_region": THORN_REEF_REGION,
                "viewed_region": THORN_REEF_REGION,
                "thorn_reef_unlocked": True,
            }
        )
        scene.start_region_unlock()

        for _ in range(5):
            scene.unlock_timer = 0
            scene.update_region_unlock(0)

        action = scene.consume_pending_action()
        self.assertEqual("ending", action["type"])
        self.assertTrue(
            action["progress_data"]["final_gate_completed"]
        )
        self.assertNotIn("open_mode", action["progress_data"])
        self.assertEqual(1, action["progress_data"]["player_bubbles"])
        self.assertEqual(0, action["progress_data"]["player_seeds"])

    def test_selected_region_gate_draws_selection_glow(self):
        nursery_end = last_level_index(DEFAULT_REGION)
        scene = MenuScene(
            progress_data={
                "current_level_index": nursery_end,
                "unlocked_levels": nursery_end,
            }
        )
        scene.mode = "levels"
        center = scene.region_gate_center()
        sample_pos = (center[0] + 28, center[1])
        plain = pygame.Surface((960, 540), pygame.SRCALPHA)
        selected = pygame.Surface((960, 540), pygame.SRCALPHA)

        scene.level_selected = nursery_end
        scene.draw_region_gate(plain)
        scene.level_selected = "gate"
        scene.draw_region_gate(selected)

        self.assertEqual(0, plain.get_at(sample_pos).a)
        self.assertGreater(selected.get_at(sample_pos).a, 0)

    def test_unlocking_thorn_reef_marks_progress_dirty_before_quit(self):
        nursery_end = last_level_index(DEFAULT_REGION)
        progress = {
            "slot_index": 0,
            "current_level_index": nursery_end,
            "latest_level_index": nursery_end,
            "unlocked_levels": nursery_end,
            "player_bubbles": 5,
            "player_seeds": 4,
            "seed_total": 4,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": DEFAULT_REGION,
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

    def test_region_unlock_plays_release_and_burst_sounds(self):
        scene = MenuScene()
        scene.sound = RecordingSound()
        scene.mode = "unlock_anim"
        scene.unlock_player = Player((120, 150))
        scene.unlock_player.bubble_count = 1
        scene.unlock_player.seed_count = 1
        scene.unlock_emit_count = 3
        scene.unlock_timer = 0

        scene.update_region_unlock(0)

        self.assertEqual(
            ["seed_release", "bubble_burst"],
            scene.sound.played,
        )
        self.assertEqual(4, scene.unlock_emit_count)
        self.assertEqual(1, len(scene.unlock_emitted))
        self.assertEqual(0, scene.unlock_player.seed_count)
        self.assertEqual("unlock_burst", scene.mode)
        self.assertIsNotNone(scene.unlock_burst_effect)

        scene.update_region_unlock_burst(scene.unlock_burst_effect.timer)

        self.assertEqual("unlock_result", scene.mode)


if __name__ == "__main__":
    unittest.main()
