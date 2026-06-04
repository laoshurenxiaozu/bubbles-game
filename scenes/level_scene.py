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


class LevelScene:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)
        self.big_font = pygame.font.SysFont("arial", 42, bold=True)
        self.huge_font = pygame.font.SysFont("arial", 54, bold=True)
        self.level_index = 0
        self.player_bubbles = PLAYER_START_BUBBLES
        self.player_seeds = PLAYER_START_SEEDS
        self.levels = self.build_levels()
        self.reset()

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
        self.player = None
        self.intro_active = level.get("intro", False)
        self.intro_time = 0.0
        self.start_leaf = Leaf(level["start_leaf"], state="green")
        self.goal = Leaf(level["goal_leaf"], state="yellow")
        self.wild_seeds = [WildSeed(x, y) for x, y in level["wild_seeds"]]
        self.free_bubbles = [FreeBubble(x, y) for x, y in level["free_bubbles"]]
        self.dropped_seeds = []
        self.fusion_bubbles = []
        self.walls = [Wall(rect[:4], axis=rect[4] if len(rect) > 4 else "both") for rect in level["walls"]]
        self.spikes = [Spike(x, y, direction=direction) for x, y, direction in level["spikes"]]
        self.pollution_zones = [PollutionZone(rect) for rect in level["pollution_zones"]]
        self.bubble_spawn_cfg = level.get("bubble_spawn")
        self.bubble_spawned = level.get("bubble_spawned", True if self.bubble_spawn_cfg is None else False)
        self.level_souvenirs = list(level.get("souvenirs", []))
        self.state = "playing"
        self.message = ""

    def spawn_player(self):
        if self.player is None:
            level = self.levels[self.level_index]
            self.player = Player(level["player_spawn"])
            self.player.bubble_count = self.player_bubbles
            self.player.seed_count = self.player_seeds
            self.intro_active = False

    def complete_level(self):
        self.player_bubbles = self.player.bubble_count
        self.player_seeds = self.player.seed_count
        self.goal.activate()
        self.state = "won"
        self.message = "Leaf Activated - Press any move key to continue"

    def advance_level(self):
        if self.level_index + 1 >= len(self.levels):
            self.reset()
            return
        self.level_index += 1
        self.reset()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif self.state == "won" and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_a,
                    pygame.K_d,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                ):
                    self.advance_level()
                if event.key == pygame.K_ESCAPE:
                    self.state = "paused" if self.state == "playing" else "playing"
                if self.state == "playing" and self.player is None and event.key == pygame.K_d:
                    self.spawn_player()
                if self.state == "playing" and self.player and event.key == pygame.K_w:
                    seed_pos = self.player.release_seed()
                    if seed_pos:
                        bubble_x, bubble_y = seed_pos
                        self.dropped_seeds.append(DroppedSeed(bubble_x, bubble_y))
                if self.state == "playing" and self.player and event.key == pygame.K_s:
                    bubble_pos = self.player.split_bubble()
                    if bubble_pos:
                        bubble_x, bubble_y = bubble_pos
                        self.free_bubbles.append(FreeBubble(bubble_x, bubble_y, pickup_delay=0.45))

    def update(self, dt):
        if self.state != "playing":
            return

        self.intro_time += dt

        keys = pygame.key.get_pressed()
        moved = False
        if self.player:
            self.player.update(dt, keys)
            self.player.resolve_wall_collisions(self.walls)
            moved = bool(
                keys[pygame.K_a]
                or keys[pygame.K_d]
                or keys[pygame.K_LEFT]
                or keys[pygame.K_RIGHT]
            )

        if self.bubble_spawn_cfg and self.player and moved and not self.bubble_spawned:
            cfg = self.bubble_spawn_cfg
            self.free_bubbles.append(
                FreeBubble(cfg["x"], cfg["y"], pickup_delay=cfg.get("pickup_delay", 0.0))
            )
            self.bubble_spawned = True

        for seed in self.wild_seeds:
            if self.player and not seed.collected and self.player.rect.colliderect(seed.rect):
                seed.collected = True
                self.player.collect_seed()
                self.free_bubbles.append(FreeBubble(seed.x, seed.y, pickup_delay=0.35))

        for bubble in self.free_bubbles:
            if not bubble.collected:
                previous_y = bubble.update(dt)
                bubble.resolve_vertical_wall_collisions(self.walls, previous_y)
                bubble.resolve_horizontal_wall_collisions(self.walls, bubble.x)
            if self.player and not bubble.collected and bubble.can_pick_up and self.player.rect.colliderect(bubble.rect):
                bubble.collected = True
                self.player.absorb_bubble()

        self.resolve_seed_bubble_fusion()

        for seed in self.dropped_seeds:
            previous_y = seed.update_vertical_motion(dt)
            seed.resolve_vertical_wall_collisions(self.walls, previous_y)
            seed.resolve_horizontal_wall_collisions(self.walls, seed.x)

        for fusion_bubble in self.fusion_bubbles:
            previous_y = fusion_bubble.update(dt)
            fusion_bubble.resolve_vertical_wall_collisions(self.walls, previous_y)
            fusion_bubble.resolve_horizontal_wall_collisions(self.walls, fusion_bubble.x)

        self.resolve_dropped_fusion()

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

    def resolve_seed_bubble_fusion(self):
        fused_pairs = []
        for seed in self.dropped_seeds:
            if seed.collected or seed.fusion_lock > 0:
                continue
            for bubble in self.free_bubbles:
                if bubble.collected or bubble.fusion_lock > 0:
                    continue
                if seed.rect.colliderect(bubble.rect):
                    fused_pairs.append((seed, bubble))
                    break

        for seed, bubble in fused_pairs:
            self.fusion_bubbles.append(
                FusionBubble(
                    (seed.x + bubble.x) / 2,
                    (seed.y + bubble.y) / 2,
                    bubble_count=bubble.bubble_count + seed.bubble_count,
                    seed_count=bubble.seed_count + seed.seed_count,
                )
            )
            seed.collected = True
            bubble.collected = True

        self.dropped_seeds = [seed for seed in self.dropped_seeds if not seed.collected]
        self.free_bubbles = [bubble for bubble in self.free_bubbles if not bubble.collected]

    def resolve_dropped_fusion(self):
        for i, seed_a in enumerate(self.dropped_seeds):
            if seed_a.collected or seed_a.fusion_lock > 0:
                continue
            for seed_b in self.dropped_seeds[i + 1 :]:
                if seed_b.collected or seed_b.fusion_lock > 0:
                    continue
                if seed_a.rect.colliderect(seed_b.rect):
                    self.fusion_bubbles.append(
                        FusionBubble(
                            (seed_a.x + seed_b.x) / 2,
                            (seed_a.y + seed_b.y) / 2,
                            bubble_count=seed_a.bubble_count + seed_b.bubble_count,
                            seed_count=seed_a.seed_count + seed_b.seed_count,
                        )
                    )
                    seed_a.collected = True
                    seed_b.collected = True
                    break

        self.dropped_seeds = [seed for seed in self.dropped_seeds if not seed.collected]

    def draw(self, screen):
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
        hint = "Esc to continue, R to restart" if self.state == "paused" else "Press R to try again"
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
        key_font = pygame.font.SysFont("arial", int(42 * pulse), bold=True)
        key_text = key_font.render(key_label, True, WHITE)
        key_surface.blit(key_text, key_text.get_rect(center=rect.center))

        hint_surface = self.huge_font.render("to start", True, WHITE)
        block_w = title_surface.get_width() + key_surface.get_width() + hint_surface.get_width() + 30
        center_x = SCREEN_WIDTH / 2
        base_y = SCREEN_HEIGHT / 2
        x = center_x - block_w / 2
        screen.blit(title_surface, title_surface.get_rect(midleft=(x, base_y)))
        x += title_surface.get_width() + 14
        screen.blit(key_surface, key_surface.get_rect(center=(x + key_surface.get_width() / 2, base_y + 4)))
        x += key_surface.get_width() + 14
        screen.blit(hint_surface, hint_surface.get_rect(midleft=(x, base_y)))
