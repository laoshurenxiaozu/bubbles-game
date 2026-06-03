import pygame

from config import (
    BG_COLOR,
    MUTED_TEXT,
    PLAYER_START_BUBBLES,
    PLAYER_START_SEEDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WATER_COLOR_BOTTOM,
    WATER_COLOR_TOP,
)
from entities.objects import DroppedSeed, FreeBubble, Goal, Leaf, PollutionZone, Spike, Wall, WildSeed
from entities.player import Player


class LevelScene:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)
        self.big_font = pygame.font.SysFont("arial", 42, bold=True)
        self.level_index = 0
        self.player_bubbles = PLAYER_START_BUBBLES
        self.player_seeds = PLAYER_START_SEEDS
        self.levels = self.build_levels()
        self.reset()

    def build_levels(self):
        return [
            {
                "name": "Tutorial",
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
            }
        ]

    def reset(self):
        level = self.levels[self.level_index]
        self.player = None
        self.start_leaf = Leaf(level["start_leaf"], state="green")
        self.goal = Leaf(level["goal_leaf"], state="yellow")
        self.wild_seeds = [WildSeed(x, y) for x, y in level["wild_seeds"]]
        self.free_bubbles = [FreeBubble(x, y) for x, y in level["free_bubbles"]]
        self.dropped_seeds = []
        self.walls = [Wall(rect) for rect in level["walls"]]
        self.spikes = [Spike(x, y, direction=direction) for x, y, direction in level["spikes"]]
        self.pollution_zones = [PollutionZone(rect) for rect in level["pollution_zones"]]
        self.state = "playing"
        self.message = ""

    def spawn_player(self):
        if self.player is None:
            level = self.levels[self.level_index]
            self.player = Player(level["player_spawn"])
            self.player.bubble_count = self.player_bubbles
            self.player.seed_count = self.player_seeds

    def complete_level(self):
        self.player_bubbles = self.player.bubble_count
        self.player_seeds = self.player.seed_count
        self.goal.activate()
        self.state = "won"
        self.message = "Leaf Activated"

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
                if self.state == "playing" and self.player is None and event.key in (
                    pygame.K_a,
                    pygame.K_d,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                ):
                    self.spawn_player()
                if self.state == "playing" and self.player and event.key == pygame.K_w:
                    seed_pos = self.player.release_seed()
                    if seed_pos:
                        bubble_x, bubble_y = seed_pos
                        self.dropped_seeds.append(
                            DroppedSeed(bubble_x + self.player.radius + 54, bubble_y - 24)
                        )
                if self.state == "playing" and self.player and event.key == pygame.K_s:
                    bubble_pos = self.player.split_bubble()
                    if bubble_pos:
                        bubble_x, bubble_y = bubble_pos
                        self.free_bubbles.append(
                            FreeBubble(bubble_x + self.player.radius + 58, bubble_y + 14, pickup_delay=1.0)
                        )

    def update(self, dt):
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        if self.player:
            self.player.update(dt, keys)
            self.player.resolve_wall_collisions(self.walls)

        for seed in self.wild_seeds:
            if self.player and not seed.collected and self.player.rect.colliderect(seed.rect):
                seed.collected = True
                self.player.collect_seed()
                self.free_bubbles.append(FreeBubble(seed.x + 62, seed.y, pickup_delay=1.25))

        for bubble in self.free_bubbles:
            if not bubble.collected:
                previous_y = bubble.update(dt)
                bubble.resolve_vertical_wall_collisions(self.walls, previous_y)
            if self.player and not bubble.collected and bubble.can_pick_up and self.player.rect.colliderect(bubble.rect):
                bubble.collected = True
                self.player.absorb_bubble()

        for seed in self.dropped_seeds:
            previous_y = seed.update_vertical_motion(dt)
            seed.resolve_vertical_wall_collisions(self.walls, previous_y)

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

    def draw(self, screen):
        self.draw_background(screen)
        self.draw_level(screen)
        if self.player:
            self.player.draw(screen)
        self.draw_hud(screen)

        if self.state in ("paused", "won", "lost"):
            self.draw_overlay(screen)

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

    def draw_hud(self, screen):
        if self.player:
            lines = [
                "A/D move   W release seed   S split bubble   R restart   Esc pause",
                f"bubbles {self.player.bubble_count}   seeds {self.player.seed_count}   net {self.player.net_value:+d}   state {self.player.vertical_state}",
            ]
        else:
            lines = [
                "A/D or arrow key: squeeze a bubble out of the starting leaf",
                "R restart   Esc pause",
            ]
        for index, line in enumerate(lines):
            color = TEXT_COLOR if index == 0 else MUTED_TEXT
            surface = self.font.render(line, True, color)
            screen.blit(surface, (22, 18 + index * 26))

        if self.message and self.state == "playing":
            surface = self.font.render(self.message, True, TEXT_COLOR)
            screen.blit(surface, surface.get_rect(center=(SCREEN_WIDTH / 2, 32)))

    def draw_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 150))
        screen.blit(overlay, (0, 0))

        title = "Paused" if self.state == "paused" else self.message
        hint = "Esc to continue, R to restart" if self.state == "paused" else "Press R to try again"
        if self.state == "won":
            hint = "Press R to replay this prototype level"

        title_surface = self.big_font.render(title, True, TEXT_COLOR)
        hint_surface = self.font.render(hint, True, MUTED_TEXT)
        screen.blit(title_surface, title_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20)))
        screen.blit(hint_surface, hint_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)))
