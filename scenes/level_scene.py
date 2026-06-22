import math
import random
from copy import deepcopy

import pygame

from config import (
    BG_COLOR,
    ENERGY_COLOR,
    GOAL_COLOR,
    PARTICLE_COLOR,
    PARTICLE_COUNT,
    WATER_DEEP,
    WATER_SURFACE,
    BUBBLE_VENT_SPAWN_INTERVAL,
    FREE_BUBBLE_RADIUS,
    MUTED_TEXT,
    OBJECT_SPILL_PICKUP_DELAY,
    PLAYER_START_BUBBLES,
    PLAYER_START_SEEDS,
    PLAYER_SPILL_BUBBLE_LIFT,
    PLAYER_SPILL_PICKUP_DELAY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from core.fonts import brand_font, ui_font
from core.input import is_cancel, is_confirm, is_down, is_left, is_map, is_restart, is_right, is_up
from core.sounds import SoundManager
from ui.menu_effects import (
    bubble_position_at_time as animated_bubble_position,
    default_menu_bubbles,
    draw_rising_bubbles,
    draw_underwater_gradient,
)
from entities.objects import BubbleVent, BurstEffect, DroppedSeed, FreeBubble, FusionBubble, Goal, Leaf, PollutionZone, Spike, Wall, WildSeed
from entities.player import Player
from levels.level_data import build_levels


RESULT_PANEL = pygame.Rect(220, 70, 520, 400)
LEVEL_NAME_DISPLAY = {
    "Tutorial1": "教程一",
    "Tutorial2": "教程二",
    "Tutorial3": "教程三",
    "Tutorial4": "教程四",
    "Reef1": "荆棘礁一",
    "Empty": "空",
}
RESTART_HINT_TEXTS = (
    "冒险的旅途充满危险，\n还好，泡泡星拥有记忆...",
    "每一颗种子都弥足珍贵，如若可以请妥善保存",
    "泡泡星的沉浮似乎有自己的逻辑?",
    "请小心谨慎，\n为了拯救泡泡星，每一步都至关重要...",
    "吞噬会引发耗散，\n如果对操作略微改变，或许结果会不太一样？",
)
EMPTY_BUBBLE_RESTART_HINT = "泡泡的破裂，似乎并非巧合？"


class LevelScene:
    def __init__(self, level_index=0, save_manager=None, slot_index=None, save_data=None, sfx_volume=80):
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
        self.music_volume = 80
        self.sfx_volume = sfx_volume
        self.restart_hint_enabled = self.save_data.get("restart_hint_enabled", True)
        self.pause_mode = "main"
        self.current_region = self.save_data.get("current_region", "thorn_reef" if self.level_index >= 4 else "nursery")
        self.thorn_reef_unlocked = self.save_data.get("thorn_reef_unlocked", self.level_index >= 4)
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

    def make_cjk_font(self, size):
        return self.make_font(size)

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
        normalized = {}
        for key, value in state_map.items():
            try:
                normalized[int(key)] = value
            except (TypeError, ValueError):
                continue
        return normalized

    def default_save_name(self, slot_index):
        return f"存档 {slot_index + 1}"

    def slot_display_name(self, slot_index):
        if self.save_manager:
            slot = self.save_manager.get_slot(slot_index)
            if slot and slot.get("name"):
                return slot["name"]
        return self.default_save_name(slot_index)

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
        self.bubble_vents = [self._build_bubble_vent(data) for data in level.get("bubble_vents", [])]
        self.pollution_zones = [PollutionZone(rect) for rect in level["pollution_zones"]]
        if saved_state:
            self._restore_saved_level_state(saved_state)
        else:
            self.wild_seeds = [WildSeed(x, y) for x, y in level["wild_seeds"]]
            self.free_bubbles = [FreeBubble(x, y) for x, y in level["free_bubbles"]]
            self.dropped_seeds = [DroppedSeed(x, y) for x, y in level.get("initial_dropped_seeds", [])]
            self.fusion_bubbles = []
        self.bubble_spawn_cfg = level.get("bubble_spawn")
        self.bubble_spawned = level.get("bubble_spawned", True if self.bubble_spawn_cfg is None else False)
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
        return pygame.Rect(44, 38, 116, 42)

    def pause_setting_rect(self, index):
        return pygame.Rect(SCREEN_WIDTH / 2 - 190, 236 + index * 58, 380, 46)

    def pause_option_at_pos(self, pos):
        for index in range(len(self.pause_options())):
            if self.pause_tab_rect(index).collidepoint(pos):
                return index
        return None

    def pause_setting_at_pos(self, pos):
        for index in range(self.pause_settings_count()):
            if self.pause_setting_rect(index).collidepoint(pos):
                return index
        return None

    def _restore_saved_level_state(self, saved_state):
        self.wild_seeds = [
            WildSeed(seed["x"], seed["y"])
            for seed in saved_state.get("wild_seeds", [])
        ]
        for seed, data in zip(self.wild_seeds, saved_state.get("wild_seeds", [])):
            seed.collected = data.get("collected", False)

        self.free_bubbles = [
            self._build_free_bubble(data)
            for data in saved_state.get("free_bubbles", [])
        ]
        self.dropped_seeds = [
            self._build_dropped_seed(data)
            for data in saved_state.get("dropped_seeds", [])
        ]
        self.fusion_bubbles = [
            self._build_fusion_bubble(data)
            for data in saved_state.get("fusion_bubbles", [])
        ]
        self.level_souvenirs = [
            self._build_souvenir(data)
            for data in saved_state.get("souvenirs", [])
        ]

    def _build_free_bubble(self, data):
        bubble = FreeBubble(data["x"], data["y"], pickup_delay=data.get("pickup_delay", 0.0))
        bubble.collected = data.get("collected", False)
        bubble.bubble_count = data.get("bubble_count", bubble.bubble_count)
        bubble.seed_count = data.get("seed_count", bubble.seed_count)
        bubble.fusion_lock = data.get("fusion_lock", bubble.fusion_lock)
        return bubble

    def _build_dropped_seed(self, data):
        seed = DroppedSeed(data["x"], data["y"])
        seed.collected = data.get("collected", False)
        seed.bubble_count = data.get("bubble_count", seed.bubble_count)
        seed.seed_count = data.get("seed_count", seed.seed_count)
        seed.fusion_lock = data.get("fusion_lock", seed.fusion_lock)
        return seed

    def _build_fusion_bubble(self, data):
        bubble = FusionBubble(
            data["x"],
            data["y"],
            bubble_count=data.get("bubble_count", 1),
            seed_count=data.get("seed_count", 1),
        )
        bubble.fusion_lock = data.get("fusion_lock", bubble.fusion_lock)
        return bubble

    def _build_bubble_vent(self, data):
        if isinstance(data, dict):
            x = data["x"]
            y = data["y"]
            spawn_interval = data.get("spawn_interval", BUBBLE_VENT_SPAWN_INTERVAL)
        else:
            x, y = data
            spawn_interval = BUBBLE_VENT_SPAWN_INTERVAL
        return BubbleVent(x, y, spawn_interval=spawn_interval)

    def is_fusion_body(self, obj):
        return getattr(obj, "bubble_count", 0) > 0 and getattr(obj, "seed_count", 0) > 0

    def should_spill_bubble(self, first, second):
        return self.is_fusion_body(first) and self.is_fusion_body(second)

    def can_merge_pair(self, first, second):
        return not (isinstance(first, DroppedSeed) and isinstance(second, DroppedSeed))

    def get_pair_merge_result(self, first, second):
        x = (first.x + second.x) / 2
        y = (first.y + second.y) / 2
        bubble_count = first.bubble_count + second.bubble_count
        seed_count = first.seed_count + second.seed_count
        spills_bubble = self.should_spill_bubble(first, second)
        if spills_bubble:
            bubble_count -= 1
        return x, y, bubble_count, seed_count, spills_bubble

    def spill_free_bubble(self, x, y, pickup_delay=0.2):
        self.free_bubbles.append(FreeBubble(x, y, pickup_delay=pickup_delay))

    def get_player_spill_position(self, obj):
        obj_radius = getattr(obj, "radius", 0)
        bubble_radius = FREE_BUBBLE_RADIUS
        x = self.player.x
        y = obj.y - obj_radius - bubble_radius - PLAYER_SPILL_BUBBLE_LIFT
        return x, y

    def _build_souvenir(self, data):
        kind = data.get("kind")
        if kind == "seed":
            return DroppedSeed(data["x"], data["y"])
        return FreeBubble(data["x"], data["y"])

    def snapshot_level_state(self):
        return {
            "wild_seeds": [
                {"x": seed.x, "y": seed.y, "collected": seed.collected}
                for seed in self.wild_seeds
            ],
            "free_bubbles": [
                {
                    "x": bubble.x,
                    "y": bubble.y,
                    "collected": bubble.collected,
                    "pickup_delay": bubble.pickup_delay,
                    "bubble_count": bubble.bubble_count,
                    "seed_count": bubble.seed_count,
                    "fusion_lock": bubble.fusion_lock,
                }
                for bubble in self.free_bubbles
            ],
            "dropped_seeds": [
                {
                    "x": seed.x,
                    "y": seed.y,
                    "collected": seed.collected,
                    "bubble_count": seed.bubble_count,
                    "seed_count": seed.seed_count,
                    "fusion_lock": seed.fusion_lock,
                }
                for seed in self.dropped_seeds
            ],
            "fusion_bubbles": [
                {
                    "x": bubble.x,
                    "y": bubble.y,
                    "bubble_count": bubble.bubble_count,
                    "seed_count": bubble.seed_count,
                    "fusion_lock": bubble.fusion_lock,
                }
                for bubble in self.fusion_bubbles
            ],
            "souvenirs": [
                {
                    "kind": "seed" if isinstance(obj, DroppedSeed) else "bubble",
                    "x": obj.x,
                    "y": obj.y,
                }
                for obj in self.level_souvenirs
            ],
        }

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
            if self.level_index == 3 and not self.thorn_reef_unlocked:
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
        self.save_message = ""
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.save_action_index = 0
        self.save_forbid_current_slot = self.slot_index is not None
        if self.slot_index is None:
            self.save_flow = "choose_slot"
            self.save_slot_index = 0
        else:
            self.save_flow = "choose_action"
            self.save_slot_index = self.slot_index
        self.save_name_input = self.slot_display_name(self.save_slot_index)

    def save_action_options(self):
        if self.slot_index is None:
            return [("另存为新存档", "save_as_new")]
        return [
            ("覆盖当前存档", "update_current"),
            ("另存为新存档", "save_as_new"),
        ]

    def move_save_slot_selection(self, delta):
        available_slots = [0, 1, 2]
        if self.save_forbid_current_slot and self.slot_index is not None:
            available_slots = [index for index in available_slots if index != self.slot_index]
        if not available_slots:
            return
        current = self.save_slot_index if self.save_slot_index in available_slots else available_slots[0]
        index = available_slots.index(current)
        self.save_slot_index = available_slots[(index + delta) % len(available_slots)]
        self.save_name_input = self.slot_display_name(self.save_slot_index)
        self.save_message = ""

    def begin_save_name_edit(self):
        self.save_editing = True
        self.save_name_input = ""
        self.save_message = "输入名称后，再按回车保存"
        self.save_cursor_timer = 0.0

    def save_slot_summary(self, slot_index):
        slot = self.save_manager.get_slot(slot_index) if self.save_manager else None
        if not slot:
            return self.default_save_name(slot_index), "空", 0
        return (
            slot.get("name") or self.default_save_name(slot_index),
            self.display_level_name(slot.get("latest_level_name", "Empty")),
            slot.get("seed_total", 0),
        )

    def display_level_name(self, level_name):
        return LEVEL_NAME_DISPLAY.get(level_name, level_name)

    def choose_result_save_action(self, choice):
        if choice == "update_current":
            self.save_slot_index = self.slot_index
            self.save_name_input = self.slot_display_name(self.save_slot_index)
            self.save_to_slot(self.save_slot_index)
            return {"type": "menu", "progress_data": self.build_progress_data()}
        self.prepare_result_save_as_new()
        return None

    def prepare_result_save_as_new(self):
        self.save_flow = "choose_slot"
        self.save_forbid_current_slot = self.slot_index is not None
        self.save_slot_index = 0 if self.slot_index is None else (self.slot_index + 1) % 3
        if self.current_save_slot_locked(self.save_slot_index):
            self.move_save_slot_selection(1)
        self.save_name_input = self.slot_display_name(self.save_slot_index)
        self.save_message = ""

    def current_save_slot_locked(self, slot_index):
        return self.save_forbid_current_slot and self.slot_index is not None and slot_index == self.slot_index

    def select_result_save_slot(self, slot_index, begin_edit_on_repeat=False):
        if self.current_save_slot_locked(slot_index):
            return
        already_selected = self.save_slot_index == slot_index
        self.save_slot_index = slot_index
        if self.save_editing:
            return
        if begin_edit_on_repeat and already_selected:
            self.begin_save_name_edit()
        else:
            self.save_name_input = self.slot_display_name(slot_index)
            self.save_message = ""

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

    def draw_star(self, surface, center, outer_radius, color, filled=True):
        inner_radius = outer_radius * 0.46
        points = []
        for index in range(10):
            angle = -math.pi / 2 + index * (math.pi / 5)
            radius = outer_radius if index % 2 == 0 else inner_radius
            points.append(
                (
                    center[0] + math.cos(angle) * radius,
                    center[1] + math.sin(angle) * radius,
                )
            )
        if filled:
            pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, color, points, 3)

    def result_option_rect(self, index):
        width = 320
        height = 40
        left = RESULT_PANEL.left + (RESULT_PANEL.width - width) // 2
        top = RESULT_PANEL.top + 226 + index * 46 - height // 2
        return pygame.Rect(left, top, width, height)

    def result_save_action_rect(self, index):
        return self.result_save_local_action_rect(index).move(RESULT_PANEL.left, RESULT_PANEL.top)

    def result_save_slot_rect(self, index):
        return self.result_save_local_slot_rect(index).move(RESULT_PANEL.left, RESULT_PANEL.top)

    def result_save_local_action_rect(self, index):
        return pygame.Rect(72, 224 + index * 60, RESULT_PANEL.width - 144, 42)

    def result_save_local_slot_rect(self, index):
        return pygame.Rect(40, 214 + index * 48, RESULT_PANEL.width - 80, 38)

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
                if self.state == "restart_hint":
                    self.skip_restart_hint()
                    continue
                self.update_direction_key_state(event, True)
                if self.state == "results":
                    action = self.handle_result_key(event)
                    if action:
                        return action
                    continue

                if self.state == "menu":
                    if self.pause_mode == "settings":
                        if is_cancel(event):
                            self.close_pause_settings()
                        elif is_up(event):
                            self.pause_settings_index = (self.pause_settings_index - 1) % self.pause_settings_count()
                            self.sound.play("menu_move")
                        elif is_down(event):
                            self.pause_settings_index = (self.pause_settings_index + 1) % self.pause_settings_count()
                            self.sound.play("menu_move")
                        elif self.is_left_event(event):
                            if self.pause_settings_index == 0:
                                self.music_volume = max(0, self.music_volume - 10)
                            elif self.pause_settings_index == 1:
                                self.sfx_volume = max(0, self.sfx_volume - 10)
                                self.sound.set_sfx_volume(self.sfx_volume)
                            else:
                                self.restart_hint_enabled = not self.restart_hint_enabled
                            self.sound.play("menu_move")
                        elif self.is_right_event(event):
                            if self.pause_settings_index == 0:
                                self.music_volume = min(100, self.music_volume + 10)
                            elif self.pause_settings_index == 1:
                                self.sfx_volume = min(100, self.sfx_volume + 10)
                                self.sound.set_sfx_volume(self.sfx_volume)
                            else:
                                self.restart_hint_enabled = not self.restart_hint_enabled
                            self.sound.play("menu_move")
                        elif is_confirm(event):
                            if self.pause_settings_index == 2:
                                self.restart_hint_enabled = not self.restart_hint_enabled
                            self.sound.play("menu_select")
                        continue

                    pause_options = self.pause_options()
                    if self.is_restart_event(event):
                        self.restart_current_level()
                        continue
                    if self.is_map_event(event):
                        progress_data = self.build_progress_data()
                        progress_data["open_mode"] = "levels"
                        self.sound.play("menu_select")
                        return {"type": "menu", "progress_data": progress_data}
                    if is_up(event):
                        self.pause_menu_index = (self.pause_menu_index - 1) % len(pause_options)
                        self.sound.play("menu_move")
                    elif is_down(event):
                        self.pause_menu_index = (self.pause_menu_index + 1) % len(pause_options)
                        self.sound.play("menu_move")
                    elif is_confirm(event) or self.is_right_event(event):
                        _, choice = pause_options[self.pause_menu_index]
                        self.sound.play("menu_select")
                        action = self.activate_pause_choice(choice)
                        if action:
                            return action
                    elif event.key == pygame.K_ESCAPE:
                        self.resume_game()
                    continue

                if self.is_restart_event(event):
                    self.restart_current_level()
                    continue
                if self.is_map_event(event):
                    progress_data = self.build_progress_data()
                    progress_data["open_mode"] = "levels"
                    self.sound.play("menu_select")
                    return {"type": "menu", "progress_data": progress_data}
                if event.key == pygame.K_ESCAPE:
                    self.open_pause_menu()
                if self.state == "playing" and self.player is None and self.is_start_event(event):
                    self.spawn_player()
                if self.state == "playing" and self.player and self.is_release_seed_event(event):
                    seed_pos = self.player.release_seed()
                    if seed_pos:
                        bubble_x, bubble_y = seed_pos
                        self.dropped_seeds.append(DroppedSeed(bubble_x, bubble_y))
                        self.sound.play("seed_release")
                if self.state == "playing" and self.player and self.is_split_bubble_event(event):
                    bubble_pos = self.player.split_bubble()
                    if bubble_pos:
                        bubble_x, bubble_y = bubble_pos
                        self.free_bubbles.append(FreeBubble(bubble_x, bubble_y, pickup_delay=0.45))
                        self.sound.play("bubble_split")
            elif event.type == pygame.MOUSEMOTION:
                if self.state == "results":
                    if self.result_mode == "summary":
                        option_index = self.result_option_at_pos(event.pos)
                        if option_index is not None:
                            previous = self.result_menu_index
                            self.result_menu_index = option_index
                            self.play_menu_move_if_changed(previous, self.result_menu_index)
                    elif self.result_mode == "save":
                        self.update_result_save_hover(event.pos)
                    continue
                if self.state == "menu" and self.pause_mode == "main":
                    option_index = self.pause_option_at_pos(event.pos)
                    if option_index is not None:
                        previous = self.pause_menu_index
                        self.pause_menu_index = option_index
                        self.play_menu_move_if_changed(previous, self.pause_menu_index)
                elif self.state == "menu" and self.pause_mode == "settings":
                    setting_index = self.pause_setting_at_pos(event.pos)
                    if setting_index is not None:
                        previous = self.pause_settings_index
                        self.pause_settings_index = setting_index
                        self.play_menu_move_if_changed(previous, self.pause_settings_index)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "results" and event.button == 1:
                    if self.result_mode == "summary":
                        option_index = self.result_option_at_pos(event.pos)
                        if option_index is not None:
                            self.result_menu_index = option_index
                            self.sound.play("menu_select")
                            action = self.activate_result_choice(self.result_actions[option_index])
                            if action:
                                return action
                    elif self.result_mode == "save":
                        action = self.handle_result_save_click(event.pos)
                        if action:
                            return action
                    continue
                if self.state == "menu" and event.button == 1:
                    if self.pause_mode == "settings":
                        if self.pause_back_rect().collidepoint(event.pos):
                            self.sound.play("menu_select")
                            self.close_pause_settings()
                            continue
                        setting_index = self.pause_setting_at_pos(event.pos)
                        if setting_index is not None:
                            self.pause_settings_index = setting_index
                            self.sound.play("menu_select")
                            if setting_index == 2:
                                self.restart_hint_enabled = not self.restart_hint_enabled
                        continue

                    option_index = self.pause_option_at_pos(event.pos)
                    if option_index is not None:
                        self.pause_menu_index = option_index
                        _, choice = self.pause_options()[option_index]
                        self.sound.play("menu_select")
                        action = self.activate_pause_choice(choice)
                        if action:
                            return action
                    continue
            elif event.type == pygame.KEYUP:
                self.update_direction_key_state(event, False)
        return None

    def result_option_at_pos(self, pos):
        for index in range(len(self.result_actions)):
            if self.result_option_rect(index).collidepoint(pos):
                return index
        return None

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
        if self.state == "results" and self.result_mode == "save" and self.save_editing:
            self.save_cursor_timer += dt

        self._update_particles(dt)

        if self.state == "restart_hint":
            self.update_restart_hint(dt)
            return

        if self.state != "playing":
            return

        self.intro_time += dt
        if self.goal_return_timer > 0:
            self.goal_return_timer = max(0, self.goal_return_timer - dt)

        if self.player is None:
            return

        keys = pygame.key.get_pressed()

        moved = False
        if self.player:
            self.player.update(dt, keys, left_pressed=self.left_down, right_pressed=self.right_down)
            self.player.resolve_wall_collisions(self.walls)
            moved = bool(
                keys[pygame.K_a]
                or keys[pygame.K_LEFT]
                or self.left_down
                or keys[pygame.K_d]
                or self.right_down
                or keys[pygame.K_RIGHT]
            )

        if self.bubble_spawn_cfg and self.player and moved and not self.bubble_spawned:
            cfg = self.bubble_spawn_cfg
            self.free_bubbles.append(
                FreeBubble(cfg["x"], cfg["y"], pickup_delay=cfg.get("pickup_delay", 0.0))
            )
            self.bubble_spawned = True

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
                self.free_bubbles.append(FreeBubble(bubble_x, bubble_y, pickup_delay=0.15))
                self.sound.play("bubble_spawn")

        for effect in self.burst_effects:
            effect.update(dt)
        self.burst_effects = [effect for effect in self.burst_effects if not effect.done]

        self.resolve_merges()

        for zone in self.pollution_zones:
            if self.player and self.player.rect.colliderect(zone.rect):
                self.player.touch_pollution(dt)

        for spike in self.spikes:
            if self.player and spike.collides_with_circle((self.player.x, self.player.y), self.player.radius):
                self.player.burst = True
                self.sound.play("bubble_burst")
            self.resolve_spike_bursts(spike)

        if self.player and self.goal_return_timer <= 0 and self.goal.collides_with_body(self.player):
            self.complete_level()

        if self.player and self.player.is_dead():
            self.state = "lost"
            self.message = "泡泡破裂"
            self.sound.play("player_death")
            self.restart_hint_override_text = (
                EMPTY_BUBBLE_RESTART_HINT if self.player.bubble_count <= 0 else None
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

    def resolve_merges(self):
        mergeables = self.collect_mergeables()
        self.resolve_player_merges(mergeables)
        self.resolve_object_merges(mergeables)
        self.prune_collected_objects()

    def resolve_spike_bursts(self, spike):
        for wild_seed in self.wild_seeds:
            if wild_seed.collected:
                continue
            if spike.collides_with(wild_seed.rect):
                self.burst_fusion_bubble(wild_seed)

        for bubble in self.free_bubbles:
            if bubble.collected:
                continue
            if spike.collides_with(bubble.rect):
                self.burst_bubble_object(bubble)

        for fusion_bubble in self.fusion_bubbles:
            if fusion_bubble.collected:
                continue
            if spike.collides_with(fusion_bubble.rect):
                self.burst_fusion_bubble(fusion_bubble)

    def burst_bubble_object(self, bubble):
        bubble.collected = True
        bubble.bubble_count = 0
        self.burst_effects.append(BurstEffect(bubble.x, bubble.y, bubble.radius))
        self.sound.play("bubble_burst")

    def burst_fusion_bubble(self, fusion_bubble):
        if fusion_bubble.collected:
            return
        released_seeds = fusion_bubble.seed_count
        self.burst_bubble_object(fusion_bubble)
        fusion_bubble.seed_count = 0
        for index in range(released_seeds):
            offset = (index - (released_seeds - 1) / 2) * 14
            self.dropped_seeds.append(DroppedSeed(fusion_bubble.x + offset, fusion_bubble.y))

    def collect_mergeables(self):
        mergeables = []
        for obj in self.wild_seeds:
            if not obj.collected and getattr(obj, "fusion_lock", 0) <= 0:
                mergeables.append(obj)
        for obj in self.free_bubbles:
            # NOTE: pickup_delay is currently visual-only here and does not prevent merge pickup checks yet.
            if not obj.collected and obj.fusion_lock <= 0:
                mergeables.append(obj)
        for obj in self.dropped_seeds:
            if not obj.collected and obj.fusion_lock <= 0:
                mergeables.append(obj)
        for obj in self.fusion_bubbles:
            if not obj.collected and obj.fusion_lock <= 0:
                mergeables.append(obj)
        return mergeables

    def resolve_player_merges(self, mergeables):
        if not self.player:
            return

        for obj in mergeables:
            if self.player.rect.colliderect(obj.rect):
                self._merge_player_with(obj)

    def resolve_object_merges(self, mergeables):
        consumed = set()
        for i, first in enumerate(mergeables):
            if id(first) in consumed or first.collected:
                continue
            for second in mergeables[i + 1 :]:
                if id(second) in consumed or second.collected:
                    continue
                if not first.rect.colliderect(second.rect):
                    continue
                if not self.can_merge_pair(first, second):
                    continue
                self._merge_pair(first, second)
                consumed.add(id(first))
                consumed.add(id(second))
                break

    def prune_collected_objects(self):
        self.wild_seeds = [seed for seed in self.wild_seeds if not seed.collected]
        self.free_bubbles = [bubble for bubble in self.free_bubbles if not bubble.collected]
        self.dropped_seeds = [seed for seed in self.dropped_seeds if not seed.collected]
        self.fusion_bubbles = [bubble for bubble in self.fusion_bubbles if not bubble.collected]

    def _merge_player_with(self, obj):
        spills_bubble = self.is_fusion_body(obj)
        self.player.bubble_count += obj.bubble_count
        self.player.seed_count += obj.seed_count
        obj.collected = True
        # Play appropriate collection sound
        if isinstance(obj, WildSeed) or isinstance(obj, DroppedSeed):
            self.sound.play("seed_collect")
        else:
            self.sound.play("bubble_collect")
        if spills_bubble:
            self.player.bubble_count = max(0, self.player.bubble_count - 1)
            spill_x, spill_y = self.get_player_spill_position(obj)
            self.spill_free_bubble(spill_x, spill_y, pickup_delay=PLAYER_SPILL_PICKUP_DELAY)

    def _merge_pair(self, first, second):
        x, y, bubble_count, seed_count, spills_bubble = self.get_pair_merge_result(first, second)
        if spills_bubble:
            self.spill_free_bubble(x, y, pickup_delay=OBJECT_SPILL_PICKUP_DELAY)
        self.fusion_bubbles.append(FusionBubble(x, y, bubble_count=bubble_count, seed_count=seed_count))
        first.collected = True
        second.collected = True

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

    def draw_restart_hint(self, screen):
        t = min(self.restart_hint_time, self.restart_hint_duration)
        self.draw_restart_hint_background(screen, t)
        self.draw_restart_hint_icon(screen, t)
        self.draw_restart_hint_text(screen)

        if self.restart_hint_fading:
            alpha = int(255 * min(1.0, self.restart_hint_fade_time / max(0.01, self.restart_hint_fade_duration)))
            fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((0, 16, 34, alpha))
            screen.blit(fade, (0, 0))

    def draw_restart_hint_background(self, screen, t):
        light = (116, 219, 236)
        deep = (24, 35, 92)
        bg_t = self.restart_hint_background_t(t)
        top = self.mix_color(light, deep, bg_t)
        bottom_light = (70, 158, 211)
        bottom_deep = (10, 22, 58)
        bottom = self.mix_color(bottom_light, bottom_deep, bg_t)
        for y in range(SCREEN_HEIGHT):
            vertical = y / SCREEN_HEIGHT
            color = self.mix_color(top, bottom, vertical)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

    def restart_hint_background_t(self, t):
        if t < 1.25:
            return self.smoothstep(t / 1.25)
        if t > 6.35:
            return 1.0 - self.smoothstep((t - 6.35) / 1.0)
        return 1.0

    def draw_restart_hint_icon(self, screen, t):
        icon_offset_x = 23
        center = (SCREEN_WIDTH / 2 + icon_offset_x, SCREEN_HEIGHT / 2 - 15)
        root = (center[0], center[1] + 38)
        leaf_root = (root[0] + 28, root[1])
        bubble_origin = self.restart_hint_leaf_stem_origin(leaf_root)
        leaf_path = self.restart_hint_leaf_path(leaf_root)
        motion = self.restart_hint_motion(root, 39, bubble_origin)

        if t < 1.7:
            progress = 1.0 - self.smoothstep(t / 1.7)
            color = self.mix_color((88, 230, 142), (177, 154, 78), self.smoothstep(t / 1.45))
            main_line_only_progress = 0.46
            if progress > main_line_only_progress:
                points = self.partial_polyline(leaf_path, progress)
            else:
                main_path = self.restart_hint_leaf_main_path(leaf_root)
                points = self.partial_polyline(main_path, progress / main_line_only_progress)
            self.draw_glow_polyline(screen, points, color, 4, 74)

        if motion["rise_start"] <= t <= motion["landing_t"] + 0.55:
            self.draw_restart_hint_bubble(screen, t, root, bubble_origin)

        if motion["seed_start"] <= t <= motion["seed_ground_t"] + 0.12:
            self.draw_restart_hint_seed(screen, t, root, bubble_origin)

        if t >= motion["landing_t"]:
            self.draw_restart_hint_ground(screen, t, root, bubble_origin, leaf_root)

        if t >= motion["leaf_start"]:
            progress = max(0.025, self.smoothstep((t - motion["leaf_start"]) / 1.25))
            color = self.mix_color((177, 154, 78), (91, 238, 146), progress)
            self.draw_glow_polyline(screen, self.partial_polyline(leaf_path, progress), color, 4, 82)

    def draw_restart_hint_bubble(self, screen, t, root, bubble_origin=None):
        radius = 39
        center = self.restart_hint_bubble_center(t, root, radius, bubble_origin)
        motion = self.restart_hint_motion(root, radius, bubble_origin)
        color = (186, 246, 255)
        alpha = 215
        if t > motion["landing_t"] + 0.3:
            alpha = int(alpha * (1.0 - self.smoothstep((t - (motion["landing_t"] + 0.3)) / 0.16)))
        if alpha <= 0:
            return

        erase = self.smoothstep((t - motion["landing_t"]) / 0.34)
        bubble_progress = 1.0
        if t < motion["draw_end"]:
            bubble_progress = self.smoothstep((t - motion["rise_start"]) / motion["draw_duration"])
            points = self.circle_points(center, radius, progress=bubble_progress, counterclockwise=True, start_angle=math.pi)
        elif erase > 0:
            points = self.erased_bubble_points(center, radius, erase)
        else:
            swallow = self.smoothstep((t - (motion["capture_t"] - 0.18)) / 0.52) * (
                1.0 - self.smoothstep((t - (motion["capture_t"] + 0.36)) / 0.42)
            )
            points = self.bubble_points(center, radius, swallow)

        if len(points) < 2:
            return

        self.draw_glow_polyline(screen, points, color, 4, int(72 * alpha / 215), alpha=alpha)
        highlight_alpha = int(min(alpha, 150) * bubble_progress)
        highlight_full = self.circle_points((center[0] - 3, center[1] - 4), radius * 0.68, progress=0.18)
        highlight_count = max(2, int(len(highlight_full) * bubble_progress))
        highlight = highlight_full[-highlight_count:]
        if len(highlight) >= 2 and erase <= 0 and highlight_alpha > 20:
            self.draw_glow_polyline(screen, highlight, (233, 255, 255), 2, 28, alpha=highlight_alpha)

    def draw_restart_hint_seed(self, screen, t, root, bubble_origin=None):
        radius = 39
        motion = self.restart_hint_motion(root, radius, bubble_origin)
        bubble_center = self.restart_hint_bubble_center(t, root, radius, bubble_origin)
        seed_x = bubble_center[0] + 5
        appear = self.smoothstep((t - motion["seed_start"]) / 0.28)

        entry = 0.0
        if t < motion["capture_t"]:
            y = motion["seed_start_y"] + motion["seed_speed"] * (t - motion["seed_start"])
        elif t < motion["landing_t"]:
            capture_span = max(0.01, motion["seed_settle_t"] - motion["capture_t"])
            capture_entry = self.smoothstep((t - motion["capture_t"]) / capture_span)
            outside_y = bubble_center[1] + motion["seed_capture_offset"]
            inside_y = bubble_center[1] + motion["carried_seed_offset"]
            y = self.lerp(outside_y, inside_y, capture_entry)
        else:
            entry_span = max(0.01, motion["seed_ground_t"] - motion["landing_t"])
            entry = max(0.0, min(1.0, (t - motion["landing_t"]) / entry_span))
            y = self.lerp(motion["landing_y"] + motion["carried_seed_offset"], motion["seed_ground_y"], entry)

        fade = 1.0 - self.smoothstep((t - (motion["seed_ground_t"] - 0.22)) / 0.22)
        alpha = int(230 * min(appear, max(0.0, fade)))
        if alpha <= 0:
            return

        pulse = 0.72 + 0.28 * math.sin(self.time * 8.0)
        seed_width = max(4, int(13 * (1.0 - 0.42 * entry)))
        seed_height = max(4, int(19 * (1.0 - 0.68 * entry)))
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(glow, (95, 255, 149, int(58 * pulse * alpha / 230 * (1.0 - 0.35 * entry))), (35, 35), 24)
        screen.blit(glow, (seed_x - 35, y - 35))
        seed_rect = pygame.Rect(0, 0, seed_width, seed_height)
        seed_rect.center = (seed_x, y)
        pygame.draw.ellipse(screen, (110, 255, 156, alpha), seed_rect, 2)
        pygame.draw.arc(
            screen,
            (217, 255, 220, alpha),
            seed_rect.inflate(-4, -4),
            math.radians(110),
            math.radians(286),
            2,
        )

    def draw_restart_hint_ground(self, screen, t, root, bubble_origin=None, leaf_root=None):
        ground_y = root[1] + 50
        radius = 39
        motion = self.restart_hint_motion(root, radius, bubble_origin)
        cx = self.restart_hint_bubble_center(motion["landing_t"], root, radius, bubble_origin)[0]
        leaf_x = self.restart_hint_leaf_stem_origin(leaf_root)[0] if leaf_root is not None else cx - 40
        line_t = self.smoothstep((t - motion["landing_t"]) / 0.24)
        shrink = 1.0 - self.smoothstep((t - motion["leaf_start"]) / 0.3)
        half_width = 60 * line_t * shrink
        color = (205, 239, 219)
        if half_width > 1:
            pygame.draw.line(screen, color, (cx - half_width, ground_y), (cx + half_width, ground_y), 2)

        pulse_t = self.smoothstep((t - (motion["landing_t"] + 0.04)) / 0.24)
        if 0 < pulse_t < 1:
            alpha = int(150 * (1.0 - pulse_t))
            gap = 4 + 5 * pulse_t
            span = 10 + 38 * pulse_t
            pulse = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pulse_color = (234, 255, 232, alpha)
            pygame.draw.line(pulse, pulse_color, (cx - gap - span, ground_y), (cx - gap, ground_y), 2)
            pygame.draw.line(pulse, pulse_color, (cx + gap, ground_y), (cx + gap + span, ground_y), 2)
            pygame.draw.circle(pulse, (234, 255, 232, min(190, alpha + 35)), (int(cx), int(ground_y)), max(2, int(5 * (1.0 - pulse_t))))
            screen.blit(pulse, (0, 0))

        green_front_t = self.smoothstep((t - motion["green_start"]) / 0.26)
        green_tail_t = self.smoothstep((t - (motion["green_start"] + 0.09)) / 0.26)
        if green_front_t > 0:
            front_x = self.lerp(cx, leaf_x, green_front_t)
            tail_x = self.lerp(cx, leaf_x, green_tail_t)
            green_alpha = int(230 * (1.0 - self.smoothstep((t - (motion["leaf_start"] + 0.12)) / 0.18)))
            if green_alpha > 0 and abs(front_x - tail_x) > 1:
                glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(glow, (95, 255, 149, int(100 * green_alpha / 230)), (tail_x, ground_y), (front_x, ground_y), 8)
                pygame.draw.line(glow, (95, 255, 149, int(145 * green_alpha / 230)), (tail_x, ground_y), (front_x, ground_y), 4)
                screen.blit(glow, (0, 0))
                pygame.draw.line(screen, (95, 255, 149, green_alpha), (tail_x, ground_y), (front_x, ground_y), 3)
                pygame.draw.circle(screen, (165, 255, 184, min(255, green_alpha)), (int(front_x), int(ground_y)), 4)

    def draw_restart_hint_text(self, screen):
        lines = self.restart_hint_text.splitlines()
        line_height = self.hint_font.get_linesize()
        start_y = SCREEN_HEIGHT - 132 - (len(lines) - 1) * line_height / 2
        for index, line in enumerate(lines):
            text = self.hint_font.render(line, True, (236, 249, 224))
            shadow = self.hint_font.render(line, True, (15, 30, 54))
            center = (SCREEN_WIDTH / 2, start_y + index * line_height)
            screen.blit(shadow, shadow.get_rect(center=(center[0] + 2, center[1] + 2)))
            screen.blit(text, text.get_rect(center=center))

    def restart_hint_leaf_path(self, root):
        root = (float(root[0]), float(root[1]))
        joint = (root[0] - 36, root[1] - 22)
        tip = (root[0] + 108, root[1] + 22)
        stem_end = self.restart_hint_leaf_stem_origin(root)
        points = []
        points.extend(self.cubic_points(stem_end, (root[0] - 88, root[1] + 13), (root[0] - 68, root[1] - 21), joint, 70))
        points.extend(self.cubic_points(joint, (root[0] + 18, root[1] - 13), (root[0] + 72, root[1] - 1), tip, 88)[1:])
        points.extend(self.cubic_points(tip, (root[0] + 44, root[1] + 56), (root[0] - 44, root[1] + 36), joint, 86)[1:])
        points.extend(self.cubic_points(joint, (root[0] - 13, root[1] - 72), (root[0] + 72, root[1] - 25), tip, 90)[1:])
        return points

    def restart_hint_leaf_main_path(self, root):
        root = (float(root[0]), float(root[1]))
        joint = (root[0] - 36, root[1] - 22)
        tip = (root[0] + 108, root[1] + 22)
        stem_end = self.restart_hint_leaf_stem_origin(root)
        points = []
        points.extend(self.cubic_points(stem_end, (root[0] - 88, root[1] + 13), (root[0] - 68, root[1] - 21), joint, 70))
        points.extend(self.cubic_points(joint, (root[0] + 18, root[1] - 13), (root[0] + 72, root[1] - 1), tip, 88)[1:])
        return points

    def restart_hint_leaf_stem_origin(self, root):
        return (float(root[0]) - 90, float(root[1]) + 50)

    def restart_hint_motion(self, root, radius, bubble_origin=None):
        if bubble_origin is None:
            bubble_origin = root
        bubble_speed = 78.0
        seed_speed = 68.0
        rise_start = 1.68
        draw_duration = 0.83
        draw_end = rise_start + draw_duration
        seed_start = draw_end - 0.06
        seed_start_y = root[1] - 176
        start_y = bubble_origin[1]
        landing_y = root[1] + 10
        seed_capture_offset = -radius + 8
        carried_seed_offset = 7
        seed_ground_y = root[1] + 57
        capture_t = (
            start_y
            + seed_capture_offset
            - seed_start_y
            + bubble_speed * rise_start
            + seed_speed * seed_start
        ) / (bubble_speed + seed_speed)
        capture_y = start_y - bubble_speed * (capture_t - rise_start)
        landing_t = capture_t + (landing_y - capture_y) / bubble_speed
        seed_ground_t = landing_t + (seed_ground_y - (landing_y + carried_seed_offset)) / seed_speed
        seed_settle_t = capture_t + 0.46
        green_start = seed_ground_t - 0.08
        leaf_start = green_start + 0.26
        return {
            "bubble_speed": bubble_speed,
            "seed_speed": seed_speed,
            "rise_start": rise_start,
            "draw_duration": draw_duration,
            "draw_end": draw_end,
            "seed_start": seed_start,
            "seed_start_y": seed_start_y,
            "start_y": start_y,
            "capture_t": capture_t,
            "capture_y": capture_y,
            "seed_settle_t": seed_settle_t,
            "landing_t": landing_t,
            "landing_y": landing_y,
            "seed_capture_offset": seed_capture_offset,
            "carried_seed_offset": carried_seed_offset,
            "seed_ground_t": seed_ground_t,
            "seed_ground_y": seed_ground_y,
            "green_start": green_start,
            "leaf_start": leaf_start,
        }

    def restart_hint_bubble_center(self, t, root, radius, bubble_origin=None):
        if bubble_origin is None:
            bubble_origin = root
        bubble_x = bubble_origin[0] + radius
        motion = self.restart_hint_motion(root, radius, bubble_origin)
        if t < motion["capture_t"]:
            rise_t = max(0.0, t - motion["rise_start"])
            return (bubble_x, motion["start_y"] - motion["bubble_speed"] * rise_t)
        if t < motion["landing_t"]:
            sink_t = t - motion["capture_t"]
            return (bubble_x, motion["capture_y"] + motion["bubble_speed"] * sink_t)
        return (bubble_x, motion["landing_y"])

    def bubble_points(self, center, radius, swallow):
        points = []
        for index in range(90):
            angle = math.tau * index / 89
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            top_weight = max(0.0, 1.0 - abs(angle - math.tau * 0.75) / 0.38)
            if top_weight > 0:
                y += 9 * swallow * top_weight
                if swallow > 0.72 and top_weight > 0.93:
                    continue
            points.append((x, y))
        return points

    def erased_bubble_points(self, center, radius, erase):
        erase = max(0.0, min(1.0, erase))
        if erase >= 0.99:
            return []
        top_angle = -math.pi / 2
        start = top_angle + erase * math.pi
        end = top_angle + math.tau - erase * math.pi
        count = max(2, int(92 * (1.0 - erase)))
        return [
            (
                center[0] + math.cos(self.lerp(start, end, i / (count - 1))) * radius,
                center[1] + math.sin(self.lerp(start, end, i / (count - 1))) * radius,
            )
            for i in range(count)
        ]

    def circle_points(self, center, radius, progress=1.0, counterclockwise=False, start_angle=math.pi / 2):
        progress = max(0.0, min(1.0, progress))
        count = max(2, int(92 * progress))
        start = start_angle
        direction = -1 if counterclockwise else 1
        return [
            (
                center[0] + math.cos(start + direction * math.tau * progress * i / (count - 1)) * radius,
                center[1] + math.sin(start + direction * math.tau * progress * i / (count - 1)) * radius,
            )
            for i in range(count)
        ]

    def quad_points(self, p0, p1, p2, steps):
        points = []
        for index in range(steps + 1):
            t = index / steps
            one = 1.0 - t
            points.append((
                one * one * p0[0] + 2 * one * t * p1[0] + t * t * p2[0],
                one * one * p0[1] + 2 * one * t * p1[1] + t * t * p2[1],
            ))
        return points

    def cubic_points(self, p0, p1, p2, p3, steps):
        points = []
        for index in range(steps + 1):
            t = index / steps
            one = 1.0 - t
            points.append((
                one * one * one * p0[0]
                + 3 * one * one * t * p1[0]
                + 3 * one * t * t * p2[0]
                + t * t * t * p3[0],
                one * one * one * p0[1]
                + 3 * one * one * t * p1[1]
                + 3 * one * t * t * p2[1]
                + t * t * t * p3[1],
            ))
        return points

    def partial_polyline(self, points, progress):
        if not points or progress <= 0:
            return []
        if progress >= 1:
            return list(points)
        lengths = [0.0]
        total = 0.0
        for start, end in zip(points, points[1:]):
            total += math.dist(start, end)
            lengths.append(total)
        target = total * progress
        partial = [points[0]]
        for index in range(1, len(points)):
            if lengths[index] < target:
                partial.append(points[index])
                continue
            segment_length = lengths[index] - lengths[index - 1]
            local = 0.0 if segment_length <= 0 else (target - lengths[index - 1]) / segment_length
            partial.append((
                self.lerp(points[index - 1][0], points[index][0], local),
                self.lerp(points[index - 1][1], points[index][1], local),
            ))
            break
        return partial

    def draw_glow_polyline(self, screen, points, color, width, glow_alpha, alpha=255):
        if len(points) < 2:
            return
        int_points = [(int(x), int(y)) for x, y in points]
        glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.lines(glow, (*color, glow_alpha), False, int_points, width + 8)
        pygame.draw.lines(glow, (*color, min(255, glow_alpha + 20)), False, int_points, width + 4)
        screen.blit(glow, (0, 0))
        pygame.draw.lines(screen, (*color, alpha), False, int_points, width)
        cap_radius = max(2, width // 2)
        pygame.draw.circle(screen, (*color, alpha), int_points[0], cap_radius)
        pygame.draw.circle(screen, (*color, alpha), int_points[-1], cap_radius)

    def mix_color(self, first, second, t):
        t = max(0.0, min(1.0, t))
        return tuple(int(self.lerp(first[index], second[index], t)) for index in range(3))

    def smoothstep(self, t):
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    def lerp(self, start, end, t):
        return start + (end - start) * max(0.0, min(1.0, t))

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

    def add_souvenir(self, kind, x, y):
        if kind == "seed":
            self.level_souvenirs.append(DroppedSeed(x, y))
        else:
            self.level_souvenirs.append(FreeBubble(x, y))

    def draw_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 150))
        screen.blit(overlay, (0, 0))

        title = "已暂停" if self.state == "paused" else self.message
        hint = "Esc 继续，R 重开，M 返回地图" if self.state == "paused" else "按 R 重试，按 M 返回地图"

        title_surface = self.big_font.render(title, True, TEXT_COLOR)
        hint_surface = self.font.render(hint, True, MUTED_TEXT)
        screen.blit(title_surface, title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20)))
        screen.blit(hint_surface, hint_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)))

    def draw_result_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 170))
        screen.blit(overlay, (0, 0))

        panel = RESULT_PANEL
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (14, 55, 76, 238), surface.get_rect(), border_radius=26)
        pygame.draw.rect(surface, (189, 231, 240), surface.get_rect(), 3, border_radius=26)

        title = self.big_font.render("关卡完成", True, WHITE)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 48)))

        stars = int(self.stars_by_level.get(str(self.level_index), 1))
        for index in range(3):
            filled = index < stars
            color = (255, 221, 126) if filled else (162, 144, 86)
            self.draw_star(surface, (panel.width / 2 - 52 + index * 52, 120), 18, color, filled=filled)

        if self.result_mode == "summary":
            self.draw_result_summary(surface)
        else:
            if self.save_flow == "choose_action":
                self.draw_result_save_actions(surface)
            else:
                self.draw_result_save_slots(surface)

        if self.save_message:
            message_surface = self.font.render(self.save_message, True, (255, 221, 126))
            surface.blit(message_surface, message_surface.get_rect(center=(panel.width / 2, panel.height - 8)))

        screen.blit(surface, panel.topleft)

    def draw_result_summary(self, surface):
        for index, choice in enumerate(self.result_actions):
            selected = index == self.result_menu_index
            label = self.result_choice_label(choice)
            color = WHITE if selected else MUTED_TEXT
            option_surface = self.big_font.render(label, True, color)
            surface.blit(option_surface, option_surface.get_rect(center=(RESULT_PANEL.width / 2, 226 + index * 46)))

    def result_choice_label(self, choice):
        return {
            "next": "下一关",
            "restart": "重新开始",
            "save": "保存",
            "level_map": "退出",
        }.get(choice, choice)

    def draw_result_save_actions(self, surface):
        header = self.font.render("选择保存方式", True, TEXT_COLOR)
        surface.blit(header, (40, 188))
        for index, (label, _) in enumerate(self.save_action_options()):
            rect = self.result_save_local_action_rect(index)
            selected = index == self.save_action_index
            fill = (27, 92, 110, 220) if selected else (17, 63, 82, 200)
            pygame.draw.rect(surface, fill, rect, border_radius=12)
            pygame.draw.rect(surface, (208, 246, 255) if selected else (96, 148, 160), rect, 2, border_radius=12)
            option_surface = self.font.render(label, True, WHITE if selected else TEXT_COLOR)
            surface.blit(option_surface, option_surface.get_rect(center=rect.center))
        hint_surface = self.small_font.render("回车确认，Esc 返回", True, MUTED_TEXT)
        surface.blit(hint_surface, hint_surface.get_rect(center=(RESULT_PANEL.width / 2, 356)))

    def draw_result_save_slots(self, surface):
        header_text = (
            "选择另一个存档位，按回车编辑名称"
            if not self.save_editing
            else "正在编辑名称，再按回车保存"
        )
        header = self.font.render(header_text, True, TEXT_COLOR)
        surface.blit(header, (40, 180))
        for index in range(3):
            self.draw_result_save_slot(surface, index)

        current_name = self.save_name_input if self.save_name_input else self.default_save_name(self.save_slot_index)
        name_label = self.font.render(f"存档名：{current_name}", True, WHITE)
        surface.blit(name_label, (40, 372))

    def draw_result_save_slot(self, surface, index):
        rect = self.result_save_local_slot_rect(index)
        locked = self.current_save_slot_locked(index)
        selected = index == self.save_slot_index
        if locked:
            fill = (11, 40, 50, 168)
            edge = (88, 122, 132)
            text_color = MUTED_TEXT
        else:
            fill = (27, 92, 110, 220) if selected else (17, 63, 82, 200)
            edge = (208, 246, 255) if selected else (96, 148, 160)
            text_color = WHITE

        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, edge, rect, 2, border_radius=10)
        slot_name, level_name, seed_total = self.save_slot_summary(index)
        prefix_surface = self.font.render(f"存档 {index + 1}: ", True, text_color)
        surface.blit(prefix_surface, prefix_surface.get_rect(midleft=(rect.left + 12, rect.centery)))

        name_x = rect.left + 12 + prefix_surface.get_width()
        self.draw_result_save_slot_name(surface, slot_name, name_x, rect, fill, selected, text_color)

        suffix_surface = self.font.render(f" | {self.display_level_name(level_name)} | 种子 {seed_total}", True, text_color)
        suffix_x = rect.right - 12 - suffix_surface.get_width()
        surface.blit(suffix_surface, suffix_surface.get_rect(midleft=(suffix_x, rect.centery)))

    def draw_result_save_slot_name(self, surface, slot_name, name_x, rect, fill, selected, text_color):
        if selected and self.save_editing:
            cursor_visible = int(self.save_cursor_timer * 2) % 2 == 0
            name_surface = self.font.render(self.save_name_input, True, WHITE)
            surface.blit(name_surface, name_surface.get_rect(midleft=(name_x, rect.centery)))
            cursor_surface = self.font.render("_", True, WHITE if cursor_visible else fill)
            cursor_x = name_x + name_surface.get_width()
            surface.blit(cursor_surface, cursor_surface.get_rect(midleft=(cursor_x, rect.centery - 2)))
            return
        name_surface = self.font.render(slot_name, True, text_color)
        surface.blit(name_surface, name_surface.get_rect(midleft=(name_x, rect.centery)))

    def draw_intro(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 12, 20, 120))
        screen.blit(overlay, (0, 0))

        prompt_font = self.make_font(42)
        title_surface = prompt_font.render("按", True, WHITE)
        pulse = 1.0 + 0.06 * math.sin(self.intro_time * 6.0)
        key_size = int(58 * pulse)
        d_key_surface = self.draw_start_key_surface("D", key_size, pulse)
        right_key_surface = self.draw_start_key_surface("right", key_size, pulse)
        slash_surface = prompt_font.render("/", True, WHITE)
        hint_surface = prompt_font.render("开始", True, WHITE)
        block_w = (
            title_surface.get_width()
            + d_key_surface.get_width()
            + slash_surface.get_width()
            + right_key_surface.get_width()
            + hint_surface.get_width()
            + 46
        )
        center_x = SCREEN_WIDTH / 2
        base_y = SCREEN_HEIGHT / 2
        x = center_x - block_w / 2
        screen.blit(title_surface, title_surface.get_rect(midleft=(x, base_y)))
        x += title_surface.get_width() + 12
        screen.blit(d_key_surface, d_key_surface.get_rect(center=(x + d_key_surface.get_width() / 2, base_y + 2)))
        x += d_key_surface.get_width() + 12
        screen.blit(slash_surface, slash_surface.get_rect(midleft=(x, base_y)))
        x += slash_surface.get_width() + 12
        screen.blit(right_key_surface, right_key_surface.get_rect(center=(x + right_key_surface.get_width() / 2, base_y + 2)))
        x += right_key_surface.get_width() + 14
        screen.blit(hint_surface, hint_surface.get_rect(midleft=(x, base_y)))

    def draw_start_key_surface(self, label, key_size, pulse):
        key_surface = pygame.Surface((key_size, key_size), pygame.SRCALPHA)
        rect = key_surface.get_rect()
        radius = max(12, int(key_size * 0.22))
        pygame.draw.rect(key_surface, (255, 255, 255, 22), rect, border_radius=radius)
        pygame.draw.rect(key_surface, (255, 255, 255, 245), rect, 3, border_radius=radius)
        if label == "right":
            self.draw_start_right_arrow(key_surface, rect, pulse)
            return key_surface
        key_font = self.make_font(32 * pulse)
        key_text = key_font.render(label, True, WHITE)
        key_surface.blit(key_text, key_text.get_rect(center=rect.center))
        return key_surface

    def draw_start_right_arrow(self, surface, rect, pulse):
        center_y = rect.centery
        left = rect.left + int(rect.width * 0.30)
        right = rect.right - int(rect.width * 0.28)
        stroke = max(3, int(4 * pulse))
        pygame.draw.line(surface, WHITE, (left, center_y), (right, center_y), stroke)
        arrow_size = int(rect.width * 0.16)
        points = [
            (right + int(rect.width * 0.02), center_y),
            (right - arrow_size, center_y - arrow_size),
            (right - arrow_size, center_y + arrow_size),
        ]
        pygame.draw.polygon(surface, WHITE, points)

    def draw_pause_menu(self, screen):
        if self.pause_mode == "settings":
            self.draw_pause_settings(screen)
            return

        self.draw_pause_menu_background(screen)
        self.draw_pause_menu_title(screen)

        for index, (label, _) in enumerate(self.pause_options()):
            rect = self.pause_tab_rect(index)
            self.draw_pause_glass_tab(screen, rect, label, index == self.pause_menu_index)

        hint = self.font.render("方向键或 W/S 选择，回车确认", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_pause_menu_background(self, screen):
        draw_underwater_gradient(screen)
        draw_rising_bubbles(screen, self.menu_bubbles, self.time)

    def menu_bubble_position_at_time(self, bubble, elapsed):
        return animated_bubble_position(bubble, elapsed)

    def draw_pause_menu_title(self, screen):
        title = self.title_font.render("暂停", True, WHITE)
        shadow = self.title_font.render("暂停", True, (30, 95, 113))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 78)))

        subtitle = self.font.render("喘口气，再潜回深海", True, TEXT_COLOR)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)))

    def draw_pause_settings(self, screen):
        self.draw_pause_menu_background(screen)
        self.draw_pause_settings_title(screen)
        self.draw_pause_back_button(screen)

        heading = self.font.render("设置", True, TEXT_COLOR)
        screen.blit(heading, heading.get_rect(center=(SCREEN_WIDTH / 2, 190)))

        for index, (label, value) in enumerate(self.pause_settings_rows()):
            rect = self.pause_setting_rect(index)
            selected = index == self.pause_settings_index
            self.draw_pause_glass_panel(screen, rect, selected=selected)
            color = WHITE if selected else TEXT_COLOR
            label_surface = self.hint_font.render(label, True, color)
            value_surface = self.font.render(value, True, color)
            screen.blit(label_surface, label_surface.get_rect(midleft=(rect.left + 18, rect.centery)))
            screen.blit(value_surface, value_surface.get_rect(midright=(rect.right - 18, rect.centery)))

        hint = self.font.render("上下选择，左右调整", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def pause_settings_rows(self):
        return [
            ("音乐", f"{self.music_volume}%"),
            ("音效", f"{self.sfx_volume}%"),
            ("重开时显示提示动画", "开" if self.restart_hint_enabled else "关"),
        ]

    def pause_settings_count(self):
        return len(self.pause_settings_rows())

    def draw_pause_settings_title(self, screen):
        title = self.brand_font.render("Bubbles", True, WHITE)
        shadow = self.brand_font.render("Bubbles", True, (30, 95, 113))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 78)))

        subtitle = self.font.render("携生命种子，从深海回到陆地", True, TEXT_COLOR)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)))

    def draw_pause_back_button(self, screen):
        rect = self.pause_back_rect()
        self.draw_pause_glass_panel(screen, rect, selected=False)
        label = self.font.render("返回", True, TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_pause_glass_tab(self, screen, rect, label, selected):
        self.draw_pause_glass_panel(screen, rect, selected)
        if selected:
            pygame.draw.circle(screen, ENERGY_COLOR, (rect.left + 28, rect.centery), 5)
        text = self.big_font.render(label, True, WHITE if selected else TEXT_COLOR)
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_pause_glass_panel(self, screen, rect, selected):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill = (235, 250, 255, 48 if selected else 30)
        edge = (226, 250, 255, 210 if selected else 130)
        shine = (255, 255, 255, 54 if selected else 30)
        pygame.draw.rect(surface, fill, surface.get_rect(), border_radius=8)
        pygame.draw.rect(surface, edge, surface.get_rect(), 2, border_radius=8)
        pygame.draw.line(surface, shine, (18, 10), (rect.width - 18, 10), 2)
        if selected:
            pygame.draw.rect(surface, (*GOAL_COLOR, 35), surface.get_rect().inflate(-8, -8), border_radius=6)
        screen.blit(surface, rect)

    def pause_tab_rect(self, index):
        width = 340
        height = 54
        gap = 14
        top = 190
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)
