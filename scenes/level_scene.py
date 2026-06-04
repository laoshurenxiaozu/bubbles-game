import math

import pygame

from config import (
    BG_COLOR,
    MUTED_TEXT,
    PLAYER_START_BUBBLES,
    PLAYER_START_SEEDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
    WATER_COLOR_BOTTOM,
    WATER_COLOR_TOP,
)
from entities.objects import DroppedSeed, FreeBubble, FusionBubble, Goal, Leaf, PollutionZone, Spike, Wall, WildSeed
from entities.player import Player


SDL_SCANCODE_D = 7


class LevelScene:
    def __init__(self, level_index=0):
        self.font = self.make_font(20)
        self.big_font = self.make_font(42)
        self.huge_font = self.make_font(54)
        self.title_font = self.make_font(64)
        self.level_index = 0
        self.player_bubbles = PLAYER_START_BUBBLES
        self.player_seeds = PLAYER_START_SEEDS
        self.levels = self.build_levels()
        self.completed_level_states = {}
        self.menu_index = 0
        self.unlocked_levels = 0
        self.requested_level_index = None
        self.menu_mode = "map"
        self.pause_menu_index = 0
        self.state = "menu"
        self.message = ""
        self.reset()
        self.open_menu()

    def make_font(self, size):
        # Use pygame's bundled default font so the game does not depend on system fonts.
        return pygame.font.Font(None, int(size))

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
                    (474, 274),
                    (892, 250),
                ],
                "free_bubbles": [],
                "pollution_zones": [],
                "intro": False,
                "bubble_spawn": {
                    "x": 300,
                    "y": 518,
                    "pickup_delay": 0.0,
                },
                "bubble_spawned": False,
            }
        ]

    def reset(self):
        level = self.levels[self.level_index]
        saved_state = self.completed_level_states.get(self.level_index)
        self.player = None
        self.intro_active = level.get("intro", False)
        self.intro_time = 0.0
        self.start_leaf = Leaf(level["start_leaf"], state="green")
        self.goal = Leaf(level["goal_leaf"], state="yellow")
        self.walls = [Wall(rect[:4], axis=rect[4] if len(rect) > 4 else "both") for rect in level["walls"]]
        self.spikes = [Spike(x, y, direction=direction) for x, y, direction in level["spikes"]]
        self.pollution_zones = [PollutionZone(rect) for rect in level["pollution_zones"]]
        if saved_state:
            self._restore_saved_level_state(saved_state)
        else:
            self.wild_seeds = [WildSeed(x, y) for x, y in level["wild_seeds"]]
            self.free_bubbles = [FreeBubble(x, y) for x, y in level["free_bubbles"]]
            self.dropped_seeds = []
            self.fusion_bubbles = []
        self.bubble_spawn_cfg = level.get("bubble_spawn")
        self.bubble_spawned = level.get("bubble_spawned", True if self.bubble_spawn_cfg is None else False)
        self.level_souvenirs = list(level.get("souvenirs", []))
        self.state = "playing"
        self.message = ""

    def open_menu(self):
        self.menu_mode = "map"
        self.state = "menu"
        self.message = ""
        self.player = None
        self.requested_level_index = None
        if self.menu_index > self.unlocked_levels:
            self.menu_index = self.unlocked_levels

    def open_pause_menu(self):
        self.menu_mode = "pause"
        self.state = "menu"
        self.pause_menu_index = 0

    def resume_game(self):
        self.state = "playing"
        self.message = ""
        self.menu_mode = "map"

    def start_level_from_menu(self, level_index):
        self.level_index = level_index
        self.requested_level_index = level_index
        self.reset()

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

    def is_fusion_body(self, obj):
        return getattr(obj, "bubble_count", 0) > 0 and getattr(obj, "seed_count", 0) > 0

    def should_spill_bubble(self, first, second):
        return self.is_fusion_body(first) and self.is_fusion_body(second)

    def spill_free_bubble(self, x, y, pickup_delay=0.2):
        self.free_bubbles.append(FreeBubble(x, y, pickup_delay=pickup_delay))

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

    def spawn_player(self):
        if self.player is None:
            level = self.levels[self.level_index]
            self.player = Player(level["player_spawn"])
            self.player.bubble_count = self.player_bubbles
            self.player.seed_count = self.player_seeds
            self.intro_active = False

    def is_start_key(self, event):
        if event.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
            return True
        if getattr(event, "scancode", None) == SDL_SCANCODE_D:
            return True
        return getattr(event, "unicode", "").lower() == "d"

    def complete_level(self):
        self.player_bubbles = self.player.bubble_count
        self.player_seeds = self.player.seed_count
        self.completed_level_states[self.level_index] = self.snapshot_level_state()
        self.unlocked_levels = max(self.unlocked_levels, self.level_index + 1)
        self.goal.activate()
        self.open_menu()
        self.message = "Level cleared"
        self.menu_index = min(self.level_index + 1, len(self.levels) - 1)
        self.player = None

    def advance_level(self):
        if self.level_index + 1 >= len(self.levels):
            self.reset()
            return
        self.level_index += 1
        self.reset()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.state == "menu" and self.menu_mode == "map":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_index = (self.menu_index - 1) % (self.unlocked_levels + 1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_index = (self.menu_index + 1) % (self.unlocked_levels + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_d, pygame.K_RIGHT):
                        self.start_level_from_menu(self.menu_index)
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    continue

                if self.state == "menu" and self.menu_mode == "pause":
                    pause_options = ("continue", "restart", "map", "settings")
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.pause_menu_index = (self.pause_menu_index - 1) % len(pause_options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.pause_menu_index = (self.pause_menu_index + 1) % len(pause_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_d, pygame.K_RIGHT):
                        choice = pause_options[self.pause_menu_index]
                        if choice == "continue":
                            self.resume_game()
                        elif choice == "restart":
                            self.reset()
                        elif choice == "map":
                            self.open_menu()
                        elif choice == "settings":
                            self.message = "Settings coming soon"
                    elif event.key == pygame.K_ESCAPE:
                        self.resume_game()
                    continue

                start_keys = (pygame.K_d, pygame.K_RIGHT)
                move_left_keys = (pygame.K_a, pygame.K_LEFT)
                move_right_keys = (pygame.K_d, pygame.K_RIGHT)
                release_seed_keys = (pygame.K_w, pygame.K_UP)
                split_bubble_keys = (pygame.K_s, pygame.K_DOWN)
                if event.key == pygame.K_r:
                    self.reset()
                elif self.state == "won" and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    *move_left_keys,
                    *move_right_keys,
                ):
                    self.advance_level()
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "playing" and self.player is None:
                    self.spawn_player()
            elif event.type == pygame.KEYUP:
                if getattr(event, "scancode", None) == SDL_SCANCODE_D:
                    self.physical_d_down = False
        return None

    def update(self, dt):
        if self.state != "playing":
            return

        self.intro_time += dt

        keys = pygame.key.get_pressed()
        if self.player is None and (
            keys[pygame.K_d]
            or self.physical_d_down
            or keys[pygame.K_RIGHT]
            or keys[pygame.K_RETURN]
            or keys[pygame.K_SPACE]
        ):
            self.spawn_player()
            return

        moved = False
        if self.player:
            self.player.update(dt, keys, right_pressed=self.physical_d_down)
            self.player.resolve_wall_collisions(self.walls)
            moved = bool(
                keys[pygame.K_a]
                or keys[pygame.K_LEFT]
                or keys[pygame.K_d]
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

        self.resolve_merges()

        self.fusion_bubbles = [bubble for bubble in self.fusion_bubbles if not bubble.collected]

        for zone in self.pollution_zones:
            if self.player and self.player.rect.colliderect(zone.rect):
                self.player.touch_pollution(dt)

        for spike in self.spikes:
            if self.player and spike.collides_with(self.player.rect):
                self.player.burst = True

        if self.player and self.player.rect.colliderect(self.goal.rect):
            self.complete_level()

        if self.player and self.player.is_dead():
            self.state = "lost"
            self.message = "Bubble Burst"

    def resolve_merges(self):
        mergeables = []
        for obj in self.wild_seeds:
            if not obj.collected and getattr(obj, "fusion_lock", 0) <= 0:
                mergeables.append(obj)
        for obj in self.free_bubbles:
            if not obj.collected and obj.fusion_lock <= 0:
                mergeables.append(obj)
        for obj in self.dropped_seeds:
            if not obj.collected and obj.fusion_lock <= 0:
                mergeables.append(obj)
        for obj in self.fusion_bubbles:
            if not obj.collected and obj.fusion_lock <= 0:
                mergeables.append(obj)

        if self.player:
            for obj in mergeables:
                if self.player.rect.colliderect(obj.rect):
                    self._merge_player_with(obj)

        consumed = set()
        for i, first in enumerate(mergeables):
            if id(first) in consumed or first.collected:
                continue
            for second in mergeables[i + 1 :]:
                if id(second) in consumed or second.collected:
                    continue
                if not first.rect.colliderect(second.rect):
                    continue
                if isinstance(first, DroppedSeed) and isinstance(second, DroppedSeed):
                    continue
                self._merge_pair(first, second)
                consumed.add(id(first))
                consumed.add(id(second))
                break

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
            self.spill_free_bubble(self.player.x, self.player.y - self.player.radius - 18)

    def _merge_pair(self, first, second):
        x = (first.x + second.x) / 2
        y = (first.y + second.y) / 2
        bubble_count = first.bubble_count + second.bubble_count
        seed_count = first.seed_count + second.seed_count
        if self.should_spill_bubble(first, second):
            bubble_count -= 1
            self.spill_free_bubble(x, y, pickup_delay=0.2)
        self.fusion_bubbles.append(FusionBubble(x, y, bubble_count=bubble_count, seed_count=seed_count))
        first.collected = True
        second.collected = True

    def draw(self, screen):
        if self.state == "menu":
            if self.menu_mode == "pause":
                self.draw_pause_menu(screen)
            else:
                self.draw_menu(screen)
            return

        self.draw_background(screen)
        self.draw_level(screen)
        for souvenir in self.level_souvenirs:
            souvenir.draw(screen)
        for fusion_bubble in self.fusion_bubbles:
            fusion_bubble.draw(screen)
        if self.player:
            self.player.draw(screen)

        if self.state in ("paused", "won", "lost"):
            self.draw_overlay(screen)
        elif self.intro_active:
            self.draw_intro(screen)

    def draw_background(self, screen):
        screen.fill(BG_COLOR)

    def draw_level(self, screen):
        self.start_leaf.draw(screen)
        self.goal.draw(screen)

        for wall in self.walls:
            wall.draw(screen)
        for spike in self.spikes:
            spike.draw(screen)

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
        hint = "Esc to continue, R to restart, M for menu" if self.state == "paused" else "Press R to try again, M for menu"
        if self.state == "won":
            hint = "Press any move key to enter the next level"

        title_surface = self.big_font.render(title, True, TEXT_COLOR)
        hint_surface = self.font.render(hint, True, MUTED_TEXT)
        screen.blit(title_surface, title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20)))
        screen.blit(hint_surface, hint_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)))

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

    def draw_menu(self, screen):
        self.draw_background(screen)

        title = self.big_font.render("Bubbles", True, WHITE)
        subtitle = self.font.render("Select a level", True, MUTED_TEXT)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 82)))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 120)))

        panel_w = 520
        panel_h = 92
        start_y = 180
        gap = 18

        for index, level in enumerate(self.levels):
            unlocked = index <= self.unlocked_levels
            selected = index == self.menu_index
            rect = pygame.Rect((SCREEN_WIDTH - panel_w) // 2, start_y + index * (panel_h + gap), panel_w, panel_h)
            fill = (24, 88, 104, 230) if unlocked else (14, 42, 52, 200)
            border = (208, 246, 255) if selected else (56, 114, 127)
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=18)
            pygame.draw.rect(panel, border, panel.get_rect(), 3, border_radius=18)

            label = f"{index + 1}. {level['name']}"
            if not unlocked:
                label += "  (locked)"
            label_surface = self.big_font.render(label, True, WHITE if unlocked else MUTED_TEXT)
            panel.blit(label_surface, (22, 18))

            hint_text = "Press D / Enter to start" if unlocked else "Finish previous level to unlock"
            hint_surface = self.font.render(hint_text, True, MUTED_TEXT)
            panel.blit(hint_surface, (22, 56))

            if selected:
                caret = self.big_font.render(">", True, WHITE)
                panel.blit(caret, (panel_w - 42, 24))

            screen.blit(panel, rect.topleft)

    def draw_pause_menu(self, screen):
        self.draw_background(screen)
        if self.player:
            self.draw_level(screen)
            self.player.draw(screen)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 165))
        screen.blit(overlay, (0, 0))

        title = self.title_font.render("Paused", True, WHITE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 120)))

        options = [
            "Continue",
            "Restart",
            "Map",
            "Settings",
        ]
        start_y = 220
        for index, option in enumerate(options):
            selected = index == self.pause_menu_index
            color = WHITE if selected else MUTED_TEXT
            label = self.big_font.render(option, True, color)
            x = SCREEN_WIDTH / 2 - label.get_width() / 2
            y = start_y + index * 62
            screen.blit(label, (x, y))
            if selected:
                caret = self.big_font.render(">", True, WHITE)
                screen.blit(caret, (x - 42, y))
