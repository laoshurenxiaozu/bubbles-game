import math
import random
from copy import deepcopy

import pygame

from config import (
    PARTICLE_COLOR,
    PARTICLE_COUNT,
    WATER_DEEP,
    WATER_SURFACE,
    PLAYER_START_BUBBLES,
    PLAYER_START_SEEDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from core.fonts import brand_font, ui_font
from core.input import is_cancel, is_confirm, is_down, is_left, is_map, is_restart, is_right, is_up
from core.level_state import LevelStateCodec
from core.merge_system import BubbleMergeSystem
from core.object_spawner import LevelObjectSpawner
from core.save_flow import SaveFlowMixin
from core.sounds import SoundManager
from levels.catalog import (
    DEFAULT_REGION,
    THORN_REEF_REGION,
    level_region,
)
from ui.menu_effects import (
    bubble_position_at_time as animated_bubble_position,
    default_menu_bubbles,
)
from ui.level_intro import LevelIntroView
from ui.pause_menu import PauseMenuView
from ui.restart_hint import RestartHintOverlay
from ui.result_overlay import ResultOverlayView
from ui.widgets import (
    ControlHintVisibility,
    draw_control_hints,
    draw_status_overlay,
)
from entities.objects import DroppedSeed, FreeBubble, Leaf, PollutionZone, Spike, Wall, WildSeed
from entities.player import Player
from levels.level_data import build_levels


RESTART_HINT_TEXTS = (
    "冒险的旅途充满危险，\n还好，泡泡星拥有记忆...",
    "每一颗种子都弥足珍贵，如若可以请妥善保存",
    "泡泡星的沉浮似乎有自己的逻辑?",
    "请小心谨慎，\n为了拯救泡泡星，每一步都至关重要...",
    "吞噬会引发耗散，\n如果对操作略微改变，或许结果会不太一样？",
)
EMPTY_BUBBLE_RESTART_HINT = "泡泡的破裂，似乎并非巧合？"


class LevelScene(SaveFlowMixin):
    def __init__(
        self,
        level_index=0,
        save_manager=None,
        slot_index=None,
        save_data=None,
        sfx_volume=80,
        music_volume=80,
    ):
        self.save_manager = save_manager
        self.slot_index = slot_index
        self.save_data = save_data or {}
        self.sound = SoundManager()
        self.sound.set_sfx_volume(sfx_volume)
        self.font = self.make_font(18)
        self.big_font = self.make_font(30)
        self.small_font = self.make_font(16)
        self.huge_font = self.make_font(44)
        self.title_font = self.make_font(46)
        self.brand_font = brand_font(64)
        self.hint_font = self.make_font(20)
        self.restart_hint_overlay = RestartHintOverlay(self.hint_font)
        self.pause_menu_view = PauseMenuView(self)
        self.result_overlay_view = ResultOverlayView(self)
        self.level_intro_view = LevelIntroView(self)
        self.control_hint_visibility = ControlHintVisibility()
        self.merge_system = BubbleMergeSystem(self)
        self.object_spawner = LevelObjectSpawner(self)
        self.level_state_codec = LevelStateCodec(self)
        self.levels = build_levels()
        self.player_bubbles = self.save_data.get("player_bubbles", PLAYER_START_BUBBLES)
        self.player_seeds = self.save_data.get("player_seeds", PLAYER_START_SEEDS)
        self.level_index = max(0, min(level_index, len(self.levels) - 1))
        self.completed_level_states = self.normalize_level_state_keys(
            self.save_data.get("completed_level_states", {})
        )
        self.unlocked_levels = self.save_data.get("unlocked_levels", 0)
        self.latest_level_index = self.save_data.get("latest_level_index", self.level_index)
        self.latest_level_index = max(0, min(self.latest_level_index, len(self.levels) - 1))
        self.latest_level_name = self.save_data.get(
            "latest_level_name",
            self.levels[self.latest_level_index]["name"],
        )
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.restart_hint_enabled = self.save_data.get("restart_hint_enabled", True)
        self.pause_mode = "main"
        self.current_region = self.save_data.get(
            "current_region",
            level_region(self.level_index),
        )
        self.thorn_reef_unlocked = self.save_data.get(
            "thorn_reef_unlocked",
            self.current_region == THORN_REEF_REGION,
        )
        self.pause_menu_index = 0
        self.pause_settings_index = 0
        self.left_down = False
        self.right_down = False
        self.time = 0.0
        self.restart_hint_time = 0.0
        self.restart_hint_fade_time = 0.0
        self.restart_hint_fading = False
        self.restart_hint_fade_duration = 0.35
        self.restart_hint_duration = 7.4
        self.restart_hint_text = RESTART_HINT_TEXTS[0]
        self.restart_hint_override_text = None
        self.stars_by_level = self.save_data.get("stars_by_level", {})
        self.menu_bubbles = default_menu_bubbles()
        self.state = "menu"
        self.message = ""
        self.result_mode = "summary"
        self.result_menu_index = 0
        self.result_actions = ["next", "restart", "save", "level_map"]
        self.level_entry_bubbles = self.player_bubbles
        self.level_entry_seeds = self.player_seeds
        self.save_slot_index = slot_index if slot_index is not None else 0
        self.save_name_input = self.default_save_name(self.save_slot_index)
        self.save_message = ""
        self.save_flow = "choose_action"
        self.save_action_index = 0
        self.save_forbid_current_slot = False
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.pending_action = None
        self._gradient_surface = self._build_gradient_surface()
        self.particles = self._create_particles(PARTICLE_COUNT)
        self.reset()

    def make_font(self, size):
        return ui_font(size)

    def _build_gradient_surface(self):
        """Pre-render the deep-water vertical gradient surface."""
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(WATER_SURFACE[0] + (WATER_DEEP[0] - WATER_SURFACE[0]) * t)
            g = int(WATER_SURFACE[1] + (WATER_DEEP[1] - WATER_SURFACE[1]) * t)
            b = int(WATER_SURFACE[2] + (WATER_DEEP[2] - WATER_SURFACE[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        return surface

    def _create_particles(self, count):
        """Spawn small floating particles (plankton / marine snow)."""
        particles = []
        for _ in range(count):
            particles.append({
                "x": random.uniform(0, SCREEN_WIDTH),
                "y": random.uniform(0, SCREEN_HEIGHT),
                "size": random.uniform(0.8, 2.5),
                "speed_x": random.uniform(-12, 12),
                "speed_y": random.uniform(-8, 0.5),
                "alpha": random.randint(30, 100),
                "phase": random.uniform(0, math.tau),
            })
        return particles

    def _update_particles(self, dt):
        """Drift particles with subtle sinusoidal sway, wrapping at screen edges."""
        for p in self.particles:
            drift = math.sin(self.time * 0.7 + p["phase"]) * 5.0
            bob = math.cos(self.time * 0.5 + p["phase"]) * 1.5
            p["x"] += (p["speed_x"] + drift) * dt
            p["y"] += (p["speed_y"] + bob) * dt
            if p["y"] > SCREEN_HEIGHT + 10:
                p["y"] = -10
            elif p["y"] < -10:
                p["y"] = SCREEN_HEIGHT + 10
            if p["x"] > SCREEN_WIDTH + 10:
                p["x"] = -10
            elif p["x"] < -10:
                p["x"] = SCREEN_WIDTH + 10

    def normalize_level_state_keys(self, state_map):
        return self.level_state_codec.normalize_keys(state_map)

    def current_save_slot_index(self):
        return self.slot_index

    def reset(self):
        level = self.levels[self.level_index]
        saved_state = self.completed_level_states.get(self.level_index)
        self.capture_level_entry_progress(saved_state)
        self.player = None
        self.left_down = False
        self.right_down = False
        self.result_mode = "summary"
        self.result_menu_index = 0
        self.save_message = ""
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.intro_active = level.get("intro", False)
        self.intro_time = 0.0
        self.goal_at_start = level.get("goal_at_start", False)
        self.goal_return_delay = level.get("goal_return_delay", 0.0)
        self.goal_return_timer = 0.0
        self.start_leaf = Leaf(level["start_leaf"], state="green")
        self.goal = Leaf(level["goal_leaf"], state="gray" if self.goal_at_start else "yellow")
        self.walls = [Wall(rect[:4]) for rect in level["walls"]]
        self.spikes = [Spike(x, y, direction=direction) for x, y, direction in level["spikes"]]
        self.bubble_vents = [
            self.level_state_codec.build_bubble_vent(data)
            for data in level.get("bubble_vents", [])
        ]
        self.pollution_zones = [PollutionZone(rect) for rect in level["pollution_zones"]]
        if saved_state:
            self.level_state_codec.restore(saved_state)
            self.object_spawner.populate(level, refresh_only=True)
        else:
            self.wild_seeds = [WildSeed(x, y) for x, y in level["wild_seeds"]]
            self.object_spawner.populate(level)
            self.fusion_bubbles = []
        self.level_souvenirs = list(level.get("souvenirs", []))
        self.state = "playing"
        self.message = ""
        self.burst_effects = []
        self.particles = self._create_particles(PARTICLE_COUNT)

    def restart_current_level(self):
        restart_hint_override = self.restart_hint_override_text
        self.restart_hint_override_text = None
        self.restore_level_entry_progress()
        if self.restart_hint_enabled:
            self.begin_restart_hint(restart_hint_override)
        else:
            self.reset()

    def begin_restart_hint(self, hint_text=None):
        self.state = "restart_hint"
        self.message = ""
        self.player = None
        self.result_mode = "summary"
        self.restart_hint_time = 0.0
        self.restart_hint_fade_time = 0.0
        self.restart_hint_fading = False
        self.restart_hint_fade_duration = 0.35
        self.restart_hint_text = hint_text or random.choice(RESTART_HINT_TEXTS)
        self.reset_direction_key_state()

    def skip_restart_hint(self):
        if self.state != "restart_hint" or self.restart_hint_fading:
            return
        self.restart_hint_fading = True
        self.restart_hint_fade_time = 0.0
        self.restart_hint_fade_duration = 0.2
        self.reset_direction_key_state()

    def finish_restart_hint(self):
        self.reset_direction_key_state()
        self.restart_hint_fading = False
        self.restart_hint_fade_time = 0.0
        self.reset()

    def capture_level_entry_progress(self, saved_state):
        self.level_entry_bubbles = self.player_bubbles
        self.level_entry_seeds = self.player_seeds
        self.level_entry_state = deepcopy(saved_state) if saved_state is not None else None
        self.level_entry_completed_level_states = deepcopy(self.completed_level_states)
        self.level_entry_unlocked_levels = self.unlocked_levels
        self.level_entry_stars_by_level = deepcopy(self.stars_by_level)
        self.level_entry_current_region = self.current_region
        self.level_entry_thorn_reef_unlocked = self.thorn_reef_unlocked
        self.level_entry_latest_level_index = self.latest_level_index
        self.level_entry_latest_level_name = self.latest_level_name

    def restore_level_entry_progress(self):
        self.player_bubbles = self.level_entry_bubbles
        self.player_seeds = self.level_entry_seeds
        self.completed_level_states = deepcopy(self.level_entry_completed_level_states)
        self.unlocked_levels = self.level_entry_unlocked_levels
        self.stars_by_level = deepcopy(self.level_entry_stars_by_level)
        self.current_region = self.level_entry_current_region
        self.thorn_reef_unlocked = self.level_entry_thorn_reef_unlocked
        self.latest_level_index = self.level_entry_latest_level_index
        self.latest_level_name = self.level_entry_latest_level_name
        self.pending_action = None

    def open_pause_menu(self):
        self.state = "menu"
        self.pause_mode = "main"
        self.pause_menu_index = 0
        self.sound.play("pause_in")

    def resume_game(self):
        self.state = "playing"
        self.message = ""
        self.sound.play("pause_out")

    def pause_options(self):
        return [
            ("继续", "continue"),
            ("重新开始", "restart"),
            ("退出", "level_map"),
            ("设置", "settings"),
        ]

    def activate_pause_choice(self, choice):
        if choice == "continue":
            self.resume_game()
        elif choice == "restart":
            self.restart_current_level()
        elif choice == "level_map":
            progress_data = self.build_progress_data()
            progress_data["open_mode"] = "levels"
            return {"type": "menu", "progress_data": progress_data}
        elif choice == "settings":
            self.pause_mode = "settings"
        return None

    def is_left_event(self, event):
        return is_left(event)

    def is_right_event(self, event):
        return is_right(event)

    def is_restart_event(self, event):
        return is_restart(event)

    def is_map_event(self, event):
        return is_map(event)

    def is_release_seed_event(self, event):
        return is_up(event)

    def is_split_bubble_event(self, event):
        return is_down(event)

    def is_start_event(self, event):
        return self.is_right_event(event)

    def update_direction_key_state(self, event, pressed):
        if self.is_left_event(event):
            self.left_down = pressed
        elif self.is_right_event(event):
            self.right_down = pressed

    def reset_direction_key_state(self):
        self.left_down = False
        self.right_down = False

    def close_pause_settings(self):
        self.pause_mode = "main"

    def pause_back_rect(self):
        return self.pause_menu_view.back_rect()

    def pause_option_at_pos(self, pos):
        return self.pause_menu_view.option_at_pos(pos)

    def pause_setting_at_pos(self, pos):
        return self.pause_menu_view.setting_at_pos(pos)

    def snapshot_level_state(self):
        return self.level_state_codec.snapshot()

    def calculate_level_stars(self):
        remaining_seeds = self.count_remaining_map_seeds()
        return max(0, 3 - remaining_seeds)

    def count_remaining_map_seeds(self):
        collections = (
            self.wild_seeds,
            self.free_bubbles,
            self.dropped_seeds,
            self.fusion_bubbles,
            self.level_souvenirs,
        )
        total = 0
        for group in collections:
            for obj in group:
                if getattr(obj, "collected", False):
                    continue
                total += max(0, getattr(obj, "seed_count", 0))
        total += self.object_spawner.count_pending_seeds()
        return total

    def build_save_snapshot(self, name):
        next_level_index = min(self.unlocked_levels, len(self.levels) - 1)
        return {
            "name": name.strip() or self.default_save_name(self.save_slot_index),
            "current_level_index": next_level_index,
            "latest_level_index": self.latest_level_index,
            "latest_level_name": self.latest_level_name,
            "unlocked_levels": self.unlocked_levels,
            "player_bubbles": self.player_bubbles,
            "player_seeds": self.player_seeds,
            "seed_total": self.player_seeds,
            "completed_level_states": self.completed_level_states,
            "stars_by_level": self.stars_by_level,
            "current_region": self.current_region,
            "thorn_reef_unlocked": self.thorn_reef_unlocked,
            "restart_hint_enabled": self.restart_hint_enabled,
        }

    def build_progress_data(self):
        current_level_index = self.level_index
        if self.state == "results":
            current_level_index = min(self.unlocked_levels, len(self.levels) - 1)
        return {
            "slot_index": self.slot_index,
            "current_level_index": current_level_index,
            "latest_level_index": self.latest_level_index,
            "latest_level_name": self.latest_level_name,
            "unlocked_levels": self.unlocked_levels,
            "player_bubbles": self.player_bubbles,
            "player_seeds": self.player_seeds,
            "seed_total": self.player_seeds,
            "completed_level_states": self.completed_level_states,
            "stars_by_level": self.stars_by_level,
            "current_region": self.current_region,
            "thorn_reef_unlocked": self.thorn_reef_unlocked,
            "restart_hint_enabled": self.restart_hint_enabled,
            "has_started_game": True,
        }

    def build_region_complete_progress_data(self):
        progress_data = self.build_progress_data()
        progress_data["open_mode"] = "levels"
        progress_data["map_message"] = "下一片海域仍在准备中"
        return progress_data

    def save_to_slot(self, slot_index):
        if not self.save_manager:
            self.save_message = "存档系统不可用"
            return
        if (
            self.save_flow == "choose_slot"
            and self.save_forbid_current_slot
            and self.slot_index is not None
            and slot_index == self.slot_index
        ):
            self.save_message = "请选择另一个存档位"
            return
        self.save_slot_index = slot_index
        snapshot = self.build_save_snapshot(self.save_name_input)
        self.save_manager.save_slot(slot_index, snapshot)
        self.slot_index = slot_index
        self.save_data = snapshot
        self.save_message = f"已保存到存档 {slot_index + 1}"
        self.save_name_input = snapshot["name"]
        self.save_editing = False

    def session_progress_state(self):
        return self.build_progress_data()

    def spawn_player(self):
        if self.player is None:
            level = self.levels[self.level_index]
            self.player = Player(level["player_spawn"])
            self.player.bubble_count = self.player_bubbles
            self.player.seed_count = self.player_seeds
            self.intro_active = False
            if self.goal_at_start:
                self.start_leaf.state = "yellow"
                self.goal.state = "yellow"
                self.goal_return_timer = self.goal_return_delay
            self.sound.play("leaf_touch")

    def complete_level(self):
        self.player_bubbles = self.player.bubble_count
        self.player_seeds = self.player.seed_count
        self.sound.play("level_complete")
        self.completed_level_states[self.level_index] = self.snapshot_level_state()
        self.unlocked_levels = max(self.unlocked_levels, self.level_index + 1)
        self.latest_level_index = self.level_index
        self.latest_level_name = self.levels[self.level_index]["name"]
        self.stars_by_level[str(self.level_index)] = self.calculate_level_stars()
        self.goal.activate()
        if self.level_index == len(self.levels) - 1:
            self.pending_action = {
                "type": "ending",
                "progress_data": self.build_progress_data(),
            }
            self.message = "泡泡星已复苏"
            return
        self.state = "results"
        self.result_mode = "summary"
        self.result_menu_index = 0
        self.message = "关卡完成"
        self.save_slot_index = self.slot_index if self.slot_index is not None else 0
        self.save_name_input = self.slot_display_name(self.save_slot_index)
        self.save_message = ""

    def consume_pending_action(self):
        action = self.pending_action
        self.pending_action = None
        return action

    def advance_level(self):
        if self.level_index + 1 >= len(self.levels):
            self.reset()
            return
        self.level_index += 1
        self.reset()

    def activate_result_choice(self, choice):
        if choice == "next":
            next_level_index = self.level_index + 1
            entering_thorn_reef = (
                next_level_index < len(self.levels)
                and level_region(self.level_index) == DEFAULT_REGION
                and level_region(next_level_index) == THORN_REEF_REGION
            )
            if entering_thorn_reef and not self.thorn_reef_unlocked:
                progress_data = self.build_progress_data()
                progress_data["open_mode"] = "levels"
                progress_data["map_message"] = "消耗 4 颗种子解锁荆棘礁"
                return {"type": "menu", "progress_data": progress_data}
            if self.level_index + 1 >= len(self.levels):
                return {"type": "menu", "progress_data": self.build_region_complete_progress_data()}
            self.advance_level()
        elif choice == "restart":
            self.restart_current_level()
        elif choice == "level_map":
            progress_data = self.build_progress_data()
            progress_data["open_mode"] = "levels"
            return {"type": "menu", "progress_data": progress_data}
        elif choice == "save":
            self.begin_save_flow()
        return None

    def begin_save_flow(self):
        self.result_mode = "save"
        self.reset_save_flow()

    def choose_result_save_action(self, choice):
        if choice == "update_current":
            self.save_slot_index = self.slot_index
            self.save_name_input = self.slot_display_name(self.save_slot_index)
            self.save_to_slot(self.save_slot_index)
            return {"type": "menu", "progress_data": self.build_progress_data()}
        self.prepare_result_save_as_new()
        return None

    def prepare_result_save_as_new(self):
        return self.prepare_save_as_new()

    def current_save_slot_locked(self, slot_index):
        return self.is_save_slot_locked(slot_index)

    def select_result_save_slot(self, slot_index, begin_edit_on_repeat=False):
        return self.select_save_slot(
            slot_index,
            begin_edit_on_repeat,
        )

    def handle_result_save_text_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.save_name_input = self.save_name_input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.save_editing = False
            self.save_message = "已取消保存"
            self.save_name_input = self.slot_display_name(self.save_slot_index)
            self.sound.play("menu_select")
        elif event.key == pygame.K_RETURN:
            self.save_to_slot(self.save_slot_index)
            self.sound.play("menu_select")
            return {"type": "menu", "progress_data": self.build_progress_data()}
        elif event.unicode and event.unicode.isprintable() and len(self.save_name_input) < 18:
            self.save_name_input += event.unicode
        return None

    def result_option_rect(self, index):
        return self.result_overlay_view.option_rect(index)

    def result_save_action_rect(self, index):
        return self.result_overlay_view.save_action_rect(index)

    def result_save_slot_rect(self, index):
        return self.result_overlay_view.save_slot_rect(index)

    def handle_result_key(self, event):
        if self.result_mode == "summary":
            return self.handle_result_summary_key(event)
        return self.handle_result_save_key(event)

    def play_menu_move_if_changed(self, previous, current):
        if previous != current:
            self.sound.play("menu_move")

    def handle_result_summary_key(self, event):
        key = event.key
        if self.is_restart_event(event):
            self.sound.play("menu_select")
            return self.activate_result_choice("restart")
        if self.is_map_event(event):
            self.sound.play("menu_select")
            return self.activate_result_choice("level_map")
        if self.is_release_seed_event(event) or self.is_left_event(event):
            self.result_menu_index = (self.result_menu_index - 1) % len(self.result_actions)
            self.sound.play("menu_move")
        elif self.is_split_bubble_event(event) or self.is_right_event(event):
            self.result_menu_index = (self.result_menu_index + 1) % len(self.result_actions)
            self.sound.play("menu_move")
        elif is_confirm(event):
            self.sound.play("menu_select")
            return self.activate_result_choice(self.result_actions[self.result_menu_index])
        elif key == pygame.K_ESCAPE:
            self.sound.play("menu_select")
            return {"type": "menu", "progress_data": self.build_progress_data()}
        return None

    def handle_result_save_key(self, event):
        if self.save_flow == "choose_action":
            options = self.save_action_options()
            if is_up(event) or is_left(event):
                self.save_action_index = (self.save_action_index - 1) % len(options)
                self.sound.play("menu_move")
            elif is_down(event) or is_right(event):
                self.save_action_index = (self.save_action_index + 1) % len(options)
                self.sound.play("menu_move")
            elif event.key == pygame.K_ESCAPE:
                self.result_mode = "summary"
                self.save_message = ""
                self.sound.play("menu_select")
            elif is_confirm(event):
                _, choice = options[self.save_action_index]
                self.sound.play("menu_select")
                return self.choose_result_save_action(choice)
            return None

        if self.save_editing:
            return self.handle_result_save_text_input(event)

        if is_up(event):
            self.move_save_slot_selection(-1)
            self.sound.play("menu_move")
        elif is_down(event):
            self.move_save_slot_selection(1)
            self.sound.play("menu_move")
        elif event.key == pygame.K_ESCAPE:
            self.result_mode = "summary"
            self.save_message = ""
            self.sound.play("menu_select")
        elif event.key == pygame.K_RETURN:
            self.begin_save_name_edit()
            self.sound.play("menu_select")
        return None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.WINDOWFOCUSLOST:
                self.reset_direction_key_state()
                continue
            if event.type == pygame.KEYDOWN:
                action = self.handle_keydown_event(event)
                if action:
                    return action
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion_event(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = self.handle_mouse_button_event(event)
                if action:
                    return action
            elif event.type == pygame.KEYUP:
                self.update_direction_key_state(event, False)
        return None

    def handle_keydown_event(self, event):
        if self.state == "restart_hint":
            self.skip_restart_hint()
            return None
        self.update_direction_key_state(event, True)
        if self.state == "results":
            return self.handle_result_key(event)
        if self.state == "menu":
            return self.handle_pause_key(event)
        return self.handle_gameplay_key(event)

    def handle_pause_key(self, event):
        if self.pause_mode == "settings":
            return self.handle_pause_settings_key(event)

        pause_options = self.pause_options()
        if self.is_restart_event(event):
            self.restart_current_level()
        elif self.is_map_event(event):
            return self.build_level_map_action()
        elif is_up(event):
            self.pause_menu_index = (
                self.pause_menu_index - 1
            ) % len(pause_options)
            self.sound.play("menu_move")
        elif is_down(event):
            self.pause_menu_index = (
                self.pause_menu_index + 1
            ) % len(pause_options)
            self.sound.play("menu_move")
        elif is_confirm(event) or self.is_right_event(event):
            _, choice = pause_options[self.pause_menu_index]
            self.sound.play("menu_select")
            return self.activate_pause_choice(choice)
        elif event.key == pygame.K_ESCAPE:
            self.resume_game()
        return None

    def handle_pause_settings_key(self, event):
        if is_cancel(event):
            self.close_pause_settings()
        elif is_up(event):
            self.pause_settings_index = (
                self.pause_settings_index - 1
            ) % self.pause_settings_count()
            self.sound.play("menu_move")
        elif is_down(event):
            self.pause_settings_index = (
                self.pause_settings_index + 1
            ) % self.pause_settings_count()
            self.sound.play("menu_move")
        elif self.is_left_event(event):
            self.adjust_pause_setting(-10)
            self.sound.play("menu_move")
        elif self.is_right_event(event):
            self.adjust_pause_setting(10)
            self.sound.play("menu_move")
        elif is_confirm(event):
            if self.pause_settings_index == 2:
                self.restart_hint_enabled = not self.restart_hint_enabled
            self.sound.play("menu_select")
        return None

    def adjust_pause_setting(self, delta):
        if self.pause_settings_index == 0:
            self.music_volume = max(
                0,
                min(100, self.music_volume + delta),
            )
        elif self.pause_settings_index == 1:
            self.sfx_volume = max(
                0,
                min(100, self.sfx_volume + delta),
            )
            self.sound.set_sfx_volume(self.sfx_volume)
        else:
            self.restart_hint_enabled = not self.restart_hint_enabled

    def handle_gameplay_key(self, event):
        if self.is_restart_event(event):
            self.restart_current_level()
            return None
        if self.is_map_event(event):
            return self.build_level_map_action()
        if event.key == pygame.K_ESCAPE:
            self.open_pause_menu()
        if (
            self.state == "playing"
            and self.player is None
            and self.is_start_event(event)
        ):
            self.spawn_player()
        if (
            self.state == "playing"
            and self.player
            and self.is_release_seed_event(event)
        ):
            seed_pos = self.player.release_seed()
            if seed_pos:
                self.dropped_seeds.append(DroppedSeed(*seed_pos))
                self.sound.play("seed_release")
        if (
            self.state == "playing"
            and self.player
            and self.is_split_bubble_event(event)
        ):
            bubble_pos = self.player.split_bubble()
            if bubble_pos:
                self.free_bubbles.append(
                    FreeBubble(*bubble_pos, pickup_delay=0.45)
                )
                self.sound.play("bubble_split")
        return None

    def build_level_map_action(self):
        progress_data = self.build_progress_data()
        progress_data["open_mode"] = "levels"
        self.sound.play("menu_select")
        return {"type": "menu", "progress_data": progress_data}

    def handle_mouse_motion_event(self, event):
        if self.state == "results":
            if self.result_mode == "summary":
                option_index = self.result_option_at_pos(event.pos)
                if option_index is not None:
                    previous = self.result_menu_index
                    self.result_menu_index = option_index
                    self.play_menu_move_if_changed(
                        previous,
                        self.result_menu_index,
                    )
            elif self.result_mode == "save":
                self.update_result_save_hover(event.pos)
            return

        if self.state != "menu":
            return
        if self.pause_mode == "main":
            option_index = self.pause_option_at_pos(event.pos)
            if option_index is not None:
                previous = self.pause_menu_index
                self.pause_menu_index = option_index
                self.play_menu_move_if_changed(
                    previous,
                    self.pause_menu_index,
                )
        elif self.pause_mode == "settings":
            setting_index = self.pause_setting_at_pos(event.pos)
            if setting_index is not None:
                previous = self.pause_settings_index
                self.pause_settings_index = setting_index
                self.play_menu_move_if_changed(
                    previous,
                    self.pause_settings_index,
                )

    def handle_mouse_button_event(self, event):
        if event.button != 1:
            return None
        if self.state == "results":
            if self.result_mode == "summary":
                option_index = self.result_option_at_pos(event.pos)
                if option_index is not None:
                    self.result_menu_index = option_index
                    self.sound.play("menu_select")
                    return self.activate_result_choice(
                        self.result_actions[option_index]
                    )
            elif self.result_mode == "save":
                return self.handle_result_save_click(event.pos)
            return None
        if self.state != "menu":
            return None
        if self.pause_mode == "settings":
            if self.pause_back_rect().collidepoint(event.pos):
                self.sound.play("menu_select")
                self.close_pause_settings()
                return None
            setting_index = self.pause_setting_at_pos(event.pos)
            if setting_index is not None:
                self.pause_settings_index = setting_index
                self.sound.play("menu_select")
                if setting_index == 2:
                    self.restart_hint_enabled = (
                        not self.restart_hint_enabled
                    )
            return None

        option_index = self.pause_option_at_pos(event.pos)
        if option_index is None:
            return None
        self.pause_menu_index = option_index
        _, choice = self.pause_options()[option_index]
        self.sound.play("menu_select")
        return self.activate_pause_choice(choice)

    def result_option_at_pos(self, pos):
        return self.result_overlay_view.option_at_pos(pos)

    def update_result_save_hover(self, pos):
        if self.save_flow == "choose_action":
            for index, _ in enumerate(self.save_action_options()):
                if self.result_save_action_rect(index).collidepoint(pos):
                    previous = self.save_action_index
                    self.save_action_index = index
                    self.play_menu_move_if_changed(previous, self.save_action_index)
                    return
            return
        if self.save_editing:
            return
        for index in range(3):
            rect = self.result_save_slot_rect(index)
            if rect.collidepoint(pos):
                if not self.current_save_slot_locked(index):
                    previous = self.save_slot_index
                    self.save_slot_index = index
                    self.play_menu_move_if_changed(previous, self.save_slot_index)
                return

    def handle_result_save_click(self, pos):
        if self.save_flow == "choose_action":
            for index, (_, choice) in enumerate(self.save_action_options()):
                if self.result_save_action_rect(index).collidepoint(pos):
                    self.save_action_index = index
                    self.sound.play("menu_select")
                    return self.choose_result_save_action(choice)
            return None

        for index in range(3):
            if self.result_save_slot_rect(index).collidepoint(pos):
                self.sound.play("menu_select")
                self.select_result_save_slot(index, begin_edit_on_repeat=True)
                return None
        return None

    def update(self, dt):
        self.time += dt
        if (
            self.state == "results"
            and self.result_mode == "save"
            and self.save_editing
        ):
            self.save_cursor_timer += dt

        self._update_particles(dt)
        if self.state == "restart_hint":
            self.update_restart_hint(dt)
            return
        if self.state == "playing":
            self.update_playing(dt)

    def update_playing(self, dt):
        self.intro_time += dt
        if self.goal_return_timer > 0:
            self.goal_return_timer = max(0, self.goal_return_timer - dt)
        if self.player is None:
            return

        moved = self.update_player(dt)
        self.object_spawner.update(dt, moved=moved)
        self.update_level_objects(dt)
        self.merge_system.resolve()
        self.resolve_hazards_and_goal(dt)

    def update_player(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(
            dt,
            keys,
            left_pressed=self.left_down,
            right_pressed=self.right_down,
        )
        self.player.resolve_wall_collisions(self.walls)
        return bool(
            keys[pygame.K_a]
            or keys[pygame.K_LEFT]
            or self.left_down
            or keys[pygame.K_d]
            or self.right_down
            or keys[pygame.K_RIGHT]
        )

    def update_level_objects(self, dt):
        for seed in self.wild_seeds:
            if not seed.collected and seed.fusion_lock > 0:
                seed.fusion_lock = max(0, seed.fusion_lock - dt)

        for bubble in self.free_bubbles:
            if not bubble.collected:
                previous_y = bubble.update(dt)
                bubble.resolve_vertical_wall_collisions(self.walls, previous_y)
                bubble.resolve_horizontal_wall_collisions(self.walls, bubble.x)

        for seed in self.dropped_seeds:
            previous_y = seed.update_vertical_motion(dt)
            seed.resolve_vertical_wall_collisions(self.walls, previous_y)
            seed.resolve_horizontal_wall_collisions(self.walls, seed.x)

        for fusion_bubble in self.fusion_bubbles:
            previous_y = fusion_bubble.update(dt)
            fusion_bubble.resolve_vertical_wall_collisions(self.walls, previous_y)
            fusion_bubble.resolve_horizontal_wall_collisions(self.walls, fusion_bubble.x)

        for vent in self.bubble_vents:
            if vent.update(dt):
                bubble_x, bubble_y = vent.spawn_position()
                self.free_bubbles.append(
                    FreeBubble(
                        bubble_x,
                        bubble_y,
                        pickup_delay=0.15,
                    )
                )
                self.sound.play("bubble_spawn")

        for effect in self.burst_effects:
            effect.update(dt)
        self.burst_effects = [
            effect
            for effect in self.burst_effects
            if not effect.done
        ]

    def resolve_hazards_and_goal(self, dt):
        for zone in self.pollution_zones:
            if self.player.rect.colliderect(zone.rect):
                self.player.touch_pollution(dt)

        for spike in self.spikes:
            if spike.collides_with_circle(
                (self.player.x, self.player.y),
                self.player.radius,
            ):
                self.player.burst = True
                self.sound.play("bubble_burst")
            self.merge_system.resolve_spike_bursts(spike)

        if (
            self.goal_return_timer <= 0
            and self.goal.collides_with_body(self.player)
        ):
            self.complete_level()

        if self.player.is_dead():
            self.state = "lost"
            self.message = "泡泡破裂"
            self.sound.play("player_death")
            self.restart_hint_override_text = (
                EMPTY_BUBBLE_RESTART_HINT
                if self.player.bubble_count <= 0
                else None
            )

    def update_restart_hint(self, dt):
        if self.restart_hint_fading:
            self.restart_hint_fade_time += dt
            if self.restart_hint_fade_time >= self.restart_hint_fade_duration:
                self.finish_restart_hint()
            return

        self.restart_hint_time += dt
        if self.restart_hint_time >= self.restart_hint_duration:
            self.restart_hint_fading = True
            self.restart_hint_fade_time = self.restart_hint_time - self.restart_hint_duration
            self.restart_hint_fade_duration = 0.35
            if self.restart_hint_fade_time >= self.restart_hint_fade_duration:
                self.finish_restart_hint()

    def draw(self, screen):
        if self.state == "restart_hint":
            self.draw_restart_hint(screen)
            return
        if self.state == "menu":
            self.draw_pause_menu(screen)
            return

        self.draw_background(screen)
        self.draw_level(screen)
        for fusion_bubble in self.fusion_bubbles:
            fusion_bubble.draw(screen)
        for effect in self.burst_effects:
            effect.draw(screen)
        if self.player:
            self.player.draw(screen)

        if self.state == "results":
            self.draw_result_overlay(screen)
        elif self.state in ("paused", "lost"):
            self.draw_overlay(screen)
        elif self.intro_active:
            self.draw_intro(screen)
        elif self.state == "playing":
            self.draw_gameplay_controls(screen)

    def draw_restart_hint(self, screen):
        self.restart_hint_overlay.draw(
            screen=screen,
            elapsed=self.restart_hint_time,
            duration=self.restart_hint_duration,
            text=self.restart_hint_text,
            world_time=self.time,
            fading=self.restart_hint_fading,
            fade_time=self.restart_hint_fade_time,
            fade_duration=self.restart_hint_fade_duration,
        )

    def draw_background(self, screen):
        screen.blit(self._gradient_surface, (0, 0))
        self._draw_particles(screen)

    def _draw_particles(self, screen):
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for p in self.particles:
            flicker = 0.5 + 0.5 * math.sin(self.time * 2.0 + p["phase"])
            alpha = int(p["alpha"] * flicker)
            if alpha < 4:
                continue
            size = max(1, int(p["size"]))
            if size <= 1:
                surface.set_at((int(p["x"]), int(p["y"])), (*PARTICLE_COLOR, alpha))
            else:
                pygame.draw.circle(
                    surface,
                    (*PARTICLE_COLOR, alpha),
                    (int(p["x"]), int(p["y"])),
                    size,
                )
        screen.blit(surface, (0, 0))

    def draw_level(self, screen):
        self.start_leaf.draw(screen)
        if not self.goal_at_start or self.player is not None:
            self.goal.draw(screen)

        for wall in self.walls:
            wall.draw(screen)
        for spike in self.spikes:
            spike.draw(screen)
        for vent in self.bubble_vents:
            vent.draw(screen)

        for zone in self.pollution_zones:
            zone.draw(screen)
        for seed in self.wild_seeds:
            seed.draw(screen)
        for seed in self.dropped_seeds:
            seed.draw(screen)
        for bubble in self.free_bubbles:
            bubble.draw(screen)

        for souvenir in self.level_souvenirs:
            souvenir.draw(screen)

    def draw_overlay(self, screen):
        title = "已暂停" if self.state == "paused" else self.message
        hint = "Esc 继续，R 重开，M 返回地图" if self.state == "paused" else "按 R 重试，按 M 返回地图"
        draw_status_overlay(
            screen,
            title,
            hint,
            self.big_font,
            self.font,
        )

    def draw_gameplay_controls(self, screen):
        draw_control_hints(
            screen,
            (
                ("A/D", "移动"),
                ("W", "释放种子"),
                ("S", "分裂泡泡"),
                ("R", "重开"),
                ("M", "地图"),
                ("Esc", "暂停"),
            ),
            self.small_font,
            (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 18),
            visibility=self.control_hint_visibility,
            context=("gameplay", self.level_index),
            elapsed=self.time,
        )

    def draw_result_overlay(self, screen):
        return self.result_overlay_view.draw(screen)

    def result_choice_label(self, choice):
        return self.result_overlay_view.choice_label(choice)

    def draw_intro(self, screen):
        return self.level_intro_view.draw(screen)

    def draw_pause_menu(self, screen):
        return self.pause_menu_view.draw(screen)

    def menu_bubble_position_at_time(self, bubble, elapsed):
        return animated_bubble_position(bubble, elapsed)

    def pause_settings_rows(self):
        return self.pause_menu_view.settings_rows()

    def pause_settings_count(self):
        return len(self.pause_settings_rows())

    def pause_tab_rect(self, index):
        return self.pause_menu_view.tab_rect(index)
