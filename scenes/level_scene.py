import math
from copy import deepcopy

import pygame

from config import (
    BG_COLOR,
    ENERGY_COLOR,
    GOAL_COLOR,
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
from entities.objects import BubbleVent, BurstEffect, DroppedSeed, FreeBubble, FusionBubble, Goal, Leaf, PollutionZone, Spike, Wall, WildSeed
from entities.player import Player


SDL_SCANCODE_D = 7


class LevelScene:
    def __init__(self, level_index=0, save_manager=None, slot_index=None, save_data=None):
        self.save_manager = save_manager
        self.slot_index = slot_index
        self.save_data = save_data or {}
        self.font = self.make_font(20)
        self.big_font = self.make_font(42)
        self.huge_font = self.make_font(54)
        self.title_font = self.make_font(64)
        self.levels = self.build_levels()
        self.player_bubbles = self.save_data.get("player_bubbles", PLAYER_START_BUBBLES)
        self.player_seeds = self.save_data.get("player_seeds", PLAYER_START_SEEDS)
        self.level_index = max(0, min(level_index, len(self.levels) - 1))
        self.completed_level_states = self.normalize_level_state_keys(
            self.save_data.get("completed_level_states", {})
        )
        self.unlocked_levels = self.save_data.get("unlocked_levels", 0)
        self.current_region = self.save_data.get("current_region", "thorn_reef" if self.level_index >= 4 else "nursery")
        self.thorn_reef_unlocked = self.save_data.get("thorn_reef_unlocked", self.level_index >= 4)
        self.pause_menu_index = 0
        self.physical_d_down = False
        self.time = 0.0
        self.stars_by_level = self.save_data.get("stars_by_level", {})
        self.menu_bubbles = [
            {"x": 86, "radius": 12, "duration": 4.8, "delay": 0.0, "drift": 12},
            {"x": 182, "radius": 20, "duration": 5.8, "delay": 1.2, "drift": 18},
            {"x": 342, "radius": 8, "duration": 4.2, "delay": 2.1, "drift": 10},
            {"x": 614, "radius": 16, "duration": 5.1, "delay": 0.7, "drift": 14},
            {"x": 806, "radius": 24, "duration": 6.4, "delay": 2.8, "drift": 20},
            {"x": 900, "radius": 10, "duration": 4.5, "delay": 1.7, "drift": 12},
            {"x": 468, "radius": 7, "duration": 3.9, "delay": 3.1, "drift": 8},
            {"x": 722, "radius": 13, "duration": 5.4, "delay": 3.8, "drift": 15},
        ]
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
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.reset()

    def make_font(self, size):
        # Use pygame's bundled default font so the game does not depend on system fonts.
        return pygame.font.Font(None, int(size))

    def normalize_level_state_keys(self, state_map):
        normalized = {}
        for key, value in state_map.items():
            try:
                normalized[int(key)] = value
            except (TypeError, ValueError):
                continue
        return normalized

    def default_save_name(self, slot_index):
        return f"Slot {slot_index + 1}"

    def slot_display_name(self, slot_index):
        if self.save_manager:
            slot = self.save_manager.get_slot(slot_index)
            if slot and slot.get("name"):
                return slot["name"]
        return self.default_save_name(slot_index)

    def build_levels(self):
        return [
            {
                # Level1: Learn dive/surface & A/D horizontal movement
                "name": "Tutorial1",
                "start_leaf": (78, 235, 82, 46),
                "goal_leaf": (514, 458, 92, 52),
                "player_spawn": (118, 258),
                "player_bubbles": 1,
                "player_seeds": 0,
                "walls": [],
                "spikes": [],
                "wild_seeds": [
                    (310, 160),
                    (766, 160),
                ],
                "free_bubbles": [
                ],
                "bubble_vents": [],
                "pollution_zones": [
                ],
                "intro": True,
                "bubble_spawn": None,
            },
            {
                # Level2: Learn W to spit seeds and adjust buoyancy
                "name": "Tutorial2",
                "start_leaf": (88, 70, 82, 46),
                "goal_leaf": (804, 180, 92, 52),
                "player_spawn": (120, 124),
                "player_bubbles": 1,
                "player_seeds": 0,
                "walls": [],
                "spikes": [],
                "wild_seeds": [],
                "free_bubbles": [],
                "bubble_vents": [],
                "pollution_zones": [],
                "intro": False,
                "bubble_spawn": {
                    "x": 350,
                    "y": 512,
                    "pickup_delay": 0.0,
                },
                "bubble_spawned": False,
            },
            {
                # Level3: Learn spikes, walls & S to split bubbles and adjust buoyancy
                "name": "Tutorial3",
                "start_leaf": (58, 448, 82, 46),
                "goal_leaf": (820, 430, 92, 52),
                "player_spawn": (112, 466),
                "player_bubbles": 1,
                "player_seeds": 0,
                "walls": [
                    (0, 376, 270, 24, "horizontal"),
                    (552, 128, 362, 26, "horizontal"),
                    (748, 300, 28, 208, "vertical"),
                ],
                "spikes": [
                    (604, 152, "down"),
                    (638, 152, "down"),
                    (672, 152, "down"),
                    (706, 152, "down"),
                    (715, 304, "left"),
                    (715, 338, "left"),
                    (715, 372, "left"),
                    (715, 406, "left"),
                    (118, 400, "down"),
                    (152, 400, "down"),
                    (186, 400, "down"),
                ],
                "wild_seeds": [
                    (474, 350),
                    (892, 250),
                ],
                "free_bubbles": [],
                "bubble_vents": [],
                "pollution_zones": [],
                "intro": False,
                "bubble_spawn": {
                    "x": 300,
                    "y": 518,
                    "pickup_delay": 0.0,
                },
                "bubble_spawned": False,
            },
            {
                # Level4: Learn bubble vents & store seeds temporarily
                "name": "Tutorial4",
                "start_leaf": (26, 148, 82, 46),
                "goal_leaf": (786, 84, 92, 52),
                "player_spawn": (84, 176),
                "player_bubbles": 1,
                "player_seeds": 0,
                "walls": [
                    (218, 30, 180, 26, "horizontal"),#1
                    (676, 214, 284, 28, "horizontal"),#2
                    (458, 488, 260, 28, "horizontal"),#3
                ],
                "spikes": [
                    (240, 56, "down"),
                    (274, 56, "down"),
                    (308, 56, "down"),
                    (342, 56, "down"),#1
                    (750, 242, "down"),
                    (784, 242, "down"),
                    (818, 242, "down"),
                    (852, 242, "down"),#2
                    (484, 460, "up"),
                    (518, 460, "up"),
                    (552, 460, "up"),
                    (586, 460, "up"),
                    (620, 460, "up"),
                    (654, 460, "up"),#3
                ],
                "wild_seeds": [],
                "free_bubbles": [],
                "bubble_vents": [
                    {"x": 316, "y": 538, "spawn_interval": 1.4},
                    {"x": 818, "y": 538, "spawn_interval": 2.0},
                ],
                "initial_dropped_seeds": [
                    (610, 38),
                ],
                "pollution_zones": [],
                "intro": False,
                "bubble_spawn": None,
            },
            {
                # Level5: First stage of the next sea region
                "name": "Reef1",
                "start_leaf": (34, 248, 82, 46),
                "goal_leaf": (34, 248, 82, 46),
                "player_spawn": (92, 280),
                "player_bubbles": 1,
                "player_seeds": 0,
                "goal_at_start": True,
                "goal_return_delay": 1.0,
                "walls": [
                    (230, 42, 170, 28, "horizontal"),
                    (540, 154, 268, 28, "horizontal"),
                    (540, 338, 308, 28, "horizontal"),
                    (432, 510, 126, 28, "horizontal"),
                ],
                "spikes": [
                    (252, 70, "down"),
                    (286, 70, "down"),
                    (320, 70, "down"),
                    (354, 70, "down"),
                    (900, 34, "down"),
                    (492, 480, "up"),
                    (526, 480, "up"),
                    (710, 310, "up"),
                    (744, 310, "up"),
                    (778, 310, "up"),
                ],
                "wild_seeds": [
                    (320, 154),
                    (760, 238),
                    (782, 438),
                ],
                "free_bubbles": [
                    (320, 527),
                ],
                "bubble_vents": [
                    {"x": 916, "y": 540, "spawn_interval": 1.8},
                ],
                "initial_dropped_seeds": [],
                "pollution_zones": [],
                "intro": False,
                "bubble_spawn": None,
            }
        ]

    def reset(self):
        level = self.levels[self.level_index]
        saved_state = self.completed_level_states.get(self.level_index)
        self.level_entry_bubbles = self.player_bubbles
        self.level_entry_seeds = self.player_seeds
        self.level_entry_state = deepcopy(saved_state) if saved_state is not None else None
        self.player = None
        self.physical_d_down = False
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

    def restart_current_level(self):
        self.player_bubbles = self.level_entry_bubbles
        self.player_seeds = self.level_entry_seeds
        if self.level_entry_state is None:
            self.completed_level_states.pop(self.level_index, None)
        else:
            self.completed_level_states[self.level_index] = deepcopy(self.level_entry_state)
        self.reset()

    def open_pause_menu(self):
        self.state = "menu"
        self.pause_menu_index = 0

    def resume_game(self):
        self.state = "playing"
        self.message = ""

    def pause_options(self):
        return [
            ("Continue", "continue"),
            ("Restart", "restart"),
            ("Level Map", "level_map"),
            ("Settings", "settings"),
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
            self.message = "Settings coming soon"
        return None

    def pause_option_at_pos(self, pos):
        for index in range(len(self.pause_options())):
            if self.pause_tab_rect(index).collidepoint(pos):
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
            "latest_level_index": self.level_index,
            "latest_level_name": self.levels[self.level_index]["name"],
            "unlocked_levels": self.unlocked_levels,
            "player_bubbles": self.player_bubbles,
            "player_seeds": self.player_seeds,
            "seed_total": self.player_seeds,
            "completed_level_states": self.completed_level_states,
            "stars_by_level": self.stars_by_level,
            "current_region": self.current_region,
            "thorn_reef_unlocked": self.thorn_reef_unlocked,
        }

    def build_progress_data(self):
        return {
            "slot_index": self.slot_index,
            "current_level_index": self.level_index,
            "latest_level_index": self.level_index,
            "latest_level_name": self.levels[self.level_index]["name"],
            "unlocked_levels": self.unlocked_levels,
            "player_bubbles": self.player_bubbles,
            "player_seeds": self.player_seeds,
            "seed_total": self.player_seeds,
            "completed_level_states": self.completed_level_states,
            "stars_by_level": self.stars_by_level,
            "current_region": self.current_region,
            "thorn_reef_unlocked": self.thorn_reef_unlocked,
        }

    def build_region_complete_progress_data(self):
        progress_data = self.build_progress_data()
        progress_data["open_mode"] = "levels"
        progress_data["map_message"] = "Next sea region coming soon"
        return progress_data

    def save_to_slot(self, slot_index):
        if not self.save_manager:
            self.save_message = "Save system unavailable"
            return
        self.save_slot_index = slot_index
        snapshot = self.build_save_snapshot(self.save_name_input)
        self.save_manager.save_slot(slot_index, snapshot)
        self.slot_index = slot_index
        self.save_data = snapshot
        self.save_message = f"Saved to slot {slot_index + 1}"
        self.save_name_input = snapshot["name"]
        self.save_editing = False

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

    def complete_level(self):
        self.player_bubbles = self.player.bubble_count
        self.player_seeds = self.player.seed_count
        self.completed_level_states[self.level_index] = self.snapshot_level_state()
        self.unlocked_levels = max(self.unlocked_levels, self.level_index + 1)
        self.stars_by_level[str(self.level_index)] = self.calculate_level_stars()
        self.goal.activate()
        self.state = "results"
        self.result_mode = "summary"
        self.result_menu_index = 0
        self.message = "Level cleared"
        self.save_slot_index = self.slot_index if self.slot_index is not None else 0
        self.save_name_input = self.slot_display_name(self.save_slot_index)
        self.save_message = ""

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
                progress_data["map_message"] = "Spend 4 seeds to unlock Thorn Reef"
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
            self.result_mode = "save"
            self.save_message = ""
            self.save_editing = False
        return None

    def begin_save_name_edit(self):
        self.save_editing = True
        self.save_name_input = ""
        self.save_message = "Enter a name, then press Enter again to save"
        self.save_cursor_timer = 0.0

    def save_slot_summary(self, slot_index):
        slot = self.save_manager.get_slot(slot_index) if self.save_manager else None
        if not slot:
            return self.default_save_name(slot_index), "Empty", 0
        return (
            slot.get("name") or self.default_save_name(slot_index),
            slot.get("latest_level_name", "Empty"),
            slot.get("seed_total", 0),
        )

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

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.state == "results":
                    if self.result_mode == "summary":
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.result_menu_index = (self.result_menu_index - 1) % len(self.result_actions)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.result_menu_index = (self.result_menu_index + 1) % len(self.result_actions)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            action = self.activate_result_choice(self.result_actions[self.result_menu_index])
                            if action:
                                return action
                        elif event.key == pygame.K_ESCAPE:
                            return {"type": "menu", "progress_data": self.build_progress_data()}
                    else:
                        if self.save_editing:
                            if event.key == pygame.K_BACKSPACE:
                                self.save_name_input = self.save_name_input[:-1]
                            elif event.key == pygame.K_ESCAPE:
                                self.save_editing = False
                                self.save_message = "Save canceled"
                                self.save_name_input = self.slot_display_name(self.save_slot_index)
                            elif event.key == pygame.K_RETURN:
                                self.save_to_slot(self.save_slot_index)
                                return {"type": "menu", "progress_data": self.build_progress_data()}
                            else:
                                if event.unicode and event.unicode.isprintable() and len(self.save_name_input) < 18:
                                    self.save_name_input += event.unicode
                        else:
                            if event.key in (pygame.K_UP, pygame.K_w):
                                self.save_slot_index = (self.save_slot_index - 1) % 3
                                self.save_name_input = self.slot_display_name(self.save_slot_index)
                                self.save_message = ""
                            elif event.key in (pygame.K_DOWN, pygame.K_s):
                                self.save_slot_index = (self.save_slot_index + 1) % 3
                                self.save_name_input = self.slot_display_name(self.save_slot_index)
                                self.save_message = ""
                            elif event.key == pygame.K_ESCAPE:
                                self.result_mode = "summary"
                                self.save_message = ""
                            elif event.key == pygame.K_RETURN:
                                self.begin_save_name_edit()
                    continue

                if self.state == "menu":
                    pause_options = self.pause_options()
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.pause_menu_index = (self.pause_menu_index - 1) % len(pause_options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.pause_menu_index = (self.pause_menu_index + 1) % len(pause_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_d, pygame.K_RIGHT):
                        _, choice = pause_options[self.pause_menu_index]
                        action = self.activate_pause_choice(choice)
                        if action:
                            return action
                    elif event.key == pygame.K_ESCAPE:
                        self.resume_game()
                    continue

                start_keys = (pygame.K_d, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE)
                release_seed_keys = (pygame.K_w, pygame.K_UP)
                split_bubble_keys = (pygame.K_s, pygame.K_DOWN)
                if event.key == pygame.K_r:
                    self.restart_current_level()
                if event.key == pygame.K_ESCAPE:
                    self.open_pause_menu()
                if self.state == "playing" and self.player is None and event.key in start_keys:
                    self.spawn_player()
                if self.state == "playing" and self.player and event.key in release_seed_keys:
                    seed_pos = self.player.release_seed()
                    if seed_pos:
                        bubble_x, bubble_y = seed_pos
                        self.dropped_seeds.append(DroppedSeed(bubble_x, bubble_y))
                if self.state == "playing" and self.player and event.key in split_bubble_keys:
                    bubble_pos = self.player.split_bubble()
                    if bubble_pos:
                        bubble_x, bubble_y = bubble_pos
                        self.free_bubbles.append(FreeBubble(bubble_x, bubble_y, pickup_delay=0.45))
            elif event.type == pygame.MOUSEMOTION:
                if self.state == "menu":
                    option_index = self.pause_option_at_pos(event.pos)
                    if option_index is not None:
                        self.pause_menu_index = option_index
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "menu" and event.button == 1:
                    option_index = self.pause_option_at_pos(event.pos)
                    if option_index is not None:
                        self.pause_menu_index = option_index
                        _, choice = self.pause_options()[option_index]
                        action = self.activate_pause_choice(choice)
                        if action:
                            return action
                    continue
            elif event.type == pygame.KEYUP:
                if getattr(event, "scancode", None) == SDL_SCANCODE_D:
                    self.physical_d_down = False
        return None

    def update(self, dt):
        self.time += dt
        if self.state == "results" and self.result_mode == "save" and self.save_editing:
            self.save_cursor_timer += dt

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
            self.player.update(dt, keys, right_pressed=self.physical_d_down)
            self.player.resolve_wall_collisions(self.walls)
            moved = bool(
                keys[pygame.K_a]
                or keys[pygame.K_LEFT]
                or keys[pygame.K_d]
                or self.physical_d_down
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

        for effect in self.burst_effects:
            effect.update(dt)
        self.burst_effects = [effect for effect in self.burst_effects if not effect.done]

        self.resolve_merges()

        for zone in self.pollution_zones:
            if self.player and self.player.rect.colliderect(zone.rect):
                self.player.touch_pollution(dt)

        for spike in self.spikes:
            if self.player and spike.collides_with(self.player.rect):
                self.player.burst = True
            self.resolve_spike_bursts(spike)

        if self.player and self.goal_return_timer <= 0 and self.player.rect.colliderect(self.goal.rect):
            self.complete_level()

        if self.player and self.player.is_dead():
            self.state = "lost"
            self.message = "Bubble Burst"

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

    def draw_background(self, screen):
        screen.fill(BG_COLOR)

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

        title = "Paused" if self.state == "paused" else self.message
        hint = "Esc to continue, R to restart, M for map" if self.state == "paused" else "Press R to try again, M for map"

        title_surface = self.big_font.render(title, True, TEXT_COLOR)
        hint_surface = self.font.render(hint, True, MUTED_TEXT)
        screen.blit(title_surface, title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20)))
        screen.blit(hint_surface, hint_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)))

    def draw_result_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 170))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(220, 70, 520, 400)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (14, 55, 76, 238), surface.get_rect(), border_radius=26)
        pygame.draw.rect(surface, (189, 231, 240), surface.get_rect(), 3, border_radius=26)

        title = self.big_font.render("Level Clear", True, WHITE)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 48)))

        stars = int(self.stars_by_level.get(str(self.level_index), 1))
        for index in range(3):
            filled = index < stars
            color = (255, 221, 126) if filled else (162, 144, 86)
            self.draw_star(surface, (panel.width / 2 - 52 + index * 52, 120), 18, color, filled=filled)

        if self.result_mode == "summary":
            for index, choice in enumerate(self.result_actions):
                selected = index == self.result_menu_index
                label = "Level Map" if choice == "level_map" else choice.capitalize()
                color = WHITE if selected else MUTED_TEXT
                option_surface = self.big_font.render(label, True, color)
                surface.blit(option_surface, option_surface.get_rect(center=(panel.width / 2, 226 + index * 46)))
        else:
            header_text = (
                "Press Enter to edit a slot name"
                if not self.save_editing
                else "Editing name... Press Enter again to save"
            )
            header = self.font.render(header_text, True, TEXT_COLOR)
            surface.blit(header, (40, 188))
            for index in range(3):
                rect = pygame.Rect(40, 220 + index * 48, panel.width - 80, 38)
                selected = index == self.save_slot_index
                fill = (27, 92, 110, 220) if selected else (17, 63, 82, 200)
                pygame.draw.rect(surface, fill, rect, border_radius=10)
                pygame.draw.rect(surface, (208, 246, 255) if selected else (96, 148, 160), rect, 2, border_radius=10)
                slot_name, level_name, seed_total = self.save_slot_summary(index)
                prefix_text = f"Slot {index + 1}: "
                suffix_text = f" | {level_name} | Seeds {seed_total}"
                prefix_surface = self.font.render(prefix_text, True, WHITE)
                surface.blit(prefix_surface, prefix_surface.get_rect(midleft=(rect.left + 12, rect.centery)))

                name_x = rect.left + 12 + prefix_surface.get_width()
                if selected and self.save_editing:
                    cursor_visible = int(self.save_cursor_timer * 2) % 2 == 0
                    display_name = self.save_name_input
                    name_surface = self.font.render(display_name, True, WHITE)
                    surface.blit(name_surface, name_surface.get_rect(midleft=(name_x, rect.centery)))
                    cursor_surface = self.font.render("_", True, WHITE if cursor_visible else fill)
                    cursor_x = name_x + name_surface.get_width()
                    surface.blit(cursor_surface, cursor_surface.get_rect(midleft=(cursor_x, rect.centery - 2)))
                else:
                    name_surface = self.font.render(slot_name, True, WHITE)
                    surface.blit(name_surface, name_surface.get_rect(midleft=(name_x, rect.centery)))

                suffix_surface = self.font.render(suffix_text, True, WHITE)
                suffix_x = rect.right - 12 - suffix_surface.get_width()
                surface.blit(suffix_surface, suffix_surface.get_rect(midleft=(suffix_x, rect.centery)))

            current_name = self.save_name_input if self.save_name_input else self.default_save_name(self.save_slot_index)
            name_label = self.font.render(f"Save Name: {current_name}", True, WHITE)
            surface.blit(name_label, (40, 372))

        if self.save_message:
            message_surface = self.font.render(self.save_message, True, (255, 221, 126))
            surface.blit(message_surface, message_surface.get_rect(center=(panel.width / 2, panel.height - 8)))

        screen.blit(surface, panel.topleft)

    def draw_intro(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 12, 20, 120))
        screen.blit(overlay, (0, 0))

        title_surface = self.huge_font.render("Press", True, WHITE)
        key_label = "D"
        pulse = 1.0 + 0.06 * math.sin(self.intro_time * 6.0)
        key_size = int(74 * pulse)
        key_surface = pygame.Surface((key_size, key_size), pygame.SRCALPHA)
        rect = key_surface.get_rect()
        border_color = (255, 255, 255, 245)
        fill_color = (255, 255, 255, 22)
        pygame.draw.rect(key_surface, fill_color, rect, border_radius=18)
        pygame.draw.rect(key_surface, border_color, rect, 3, border_radius=18)
        key_font = self.make_font(42 * pulse)
        key_text = key_font.render(key_label, True, WHITE)
        key_surface.blit(key_text, key_text.get_rect(center=rect.center))

        hint_surface = self.huge_font.render("/ Right / Enter", True, WHITE)
        block_w = title_surface.get_width() + key_surface.get_width() + hint_surface.get_width() + 30
        center_x = SCREEN_WIDTH / 2
        base_y = SCREEN_HEIGHT / 2
        x = center_x - block_w / 2
        screen.blit(title_surface, title_surface.get_rect(midleft=(x, base_y)))
        x += title_surface.get_width() + 14
        screen.blit(key_surface, key_surface.get_rect(center=(x + key_surface.get_width() / 2, base_y + 4)))
        x += key_surface.get_width() + 14
        screen.blit(hint_surface, hint_surface.get_rect(midleft=(x, base_y)))

    def draw_pause_menu(self, screen):
        self.draw_pause_menu_background(screen)
        self.draw_pause_menu_title(screen)

        for index, (label, _) in enumerate(self.pause_options()):
            rect = self.pause_tab_rect(index)
            self.draw_pause_glass_tab(screen, rect, label, index == self.pause_menu_index)

        hint = self.font.render("Use arrows or W/S, Enter to choose", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_pause_menu_background(self, screen):
        screen.fill((11, 49, 68))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            color = (
                int(11 + 8 * t),
                int(49 + 35 * t),
                int(68 + 46 * t),
            )
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

        for bubble in self.menu_bubbles:
            self.draw_menu_rising_bubble(screen, bubble)

    def menu_bubble_position_at_time(self, bubble, elapsed):
        progress = ((elapsed + bubble["delay"]) % bubble["duration"]) / bubble["duration"]
        x = bubble["x"] + math.sin(progress * math.tau * 1.4 + bubble["x"]) * bubble["drift"]
        y = SCREEN_HEIGHT + 42 - progress * (SCREEN_HEIGHT + 110)
        return (int(x), int(y))

    def draw_menu_rising_bubble(self, screen, bubble):
        center = self.menu_bubble_position_at_time(bubble, self.time)
        progress = ((self.time + bubble["delay"]) % bubble["duration"]) / bubble["duration"]
        radius = bubble["radius"]
        alpha = int(210 * min(1.0, progress * 5.0, (1.0 - progress) * 5.0))
        if alpha <= 0:
            return

        bubble_surface = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        local_center = (radius * 3 // 2, radius * 3 // 2)
        pygame.draw.circle(bubble_surface, (180, 235, 255, alpha), local_center, radius, 2)
        pygame.draw.circle(
            bubble_surface,
            (244, 253, 255, min(255, alpha + 30)),
            (local_center[0] - radius // 3, local_center[1] - radius // 3),
            max(2, radius // 5),
        )
        screen.blit(bubble_surface, (center[0] - local_center[0], center[1] - local_center[1]))

    def draw_pause_menu_title(self, screen):
        title = self.title_font.render("Paused", True, WHITE)
        shadow = self.title_font.render("Paused", True, (30, 95, 113))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 78)))

        subtitle = self.font.render("Take a breath before diving back in", True, TEXT_COLOR)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)))

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
