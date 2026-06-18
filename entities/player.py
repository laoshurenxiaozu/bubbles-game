import pygame

from config import (
    HORIZONTAL_SPEED,
    PLAYER_MIN_BUBBLES,
    PLAYER_START_BUBBLES,
    PLAYER_START_SEEDS,
    POLLUTION_LIMIT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from core.physics import FloatBody


class Player(FloatBody):
    def __init__(self, pos):
        super().__init__(pos[0], pos[1], PLAYER_START_BUBBLES, PLAYER_START_SEEDS)
        self.pollution = 0
        self.burst = False
        self.previous_x = self.x
        self.previous_y = self.y

    @property
    def radius(self):
        return 22 + self.bubble_count * 7

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def update(self, dt, keys, left_pressed=False, right_pressed=False):
        self.previous_x = self.x
        self.previous_y = self.y
        horizontal = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT] or left_pressed:
            horizontal -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT] or right_pressed:
            horizontal += 1

        self.x += horizontal * HORIZONTAL_SPEED * dt
        self.update_vertical_motion(dt)

        r = self.radius
        if self.x < r:
            self.x = r
        if self.x > SCREEN_WIDTH - r:
            self.x = SCREEN_WIDTH - r
        if self.y < r:
            self.y = r
        if self.y > SCREEN_HEIGHT - r:
            self.y = SCREEN_HEIGHT - r

    def resolve_wall_collisions(self, walls):
        for wall in walls:
            radius = self.radius
            prev_left = self.previous_x - radius
            prev_right = self.previous_x + radius
            prev_top = self.previous_y - radius
            prev_bottom = self.previous_y + radius
            curr_left = self.x - radius
            curr_right = self.x + radius
            curr_top = self.y - radius
            curr_bottom = self.y + radius

            if curr_right < wall.rect.left or curr_left > wall.rect.right or curr_bottom < wall.rect.top or curr_top > wall.rect.bottom:
                continue

            if prev_bottom <= wall.rect.top and curr_bottom > wall.rect.top:
                self.y = wall.rect.top - radius
                continue
            if prev_top >= wall.rect.bottom and curr_top < wall.rect.bottom:
                self.y = wall.rect.bottom + radius
                continue
            if prev_right <= wall.rect.left and curr_right > wall.rect.left:
                self.x = wall.rect.left - radius
                continue
            if prev_left >= wall.rect.right and curr_left < wall.rect.right:
                self.x = wall.rect.right + radius
                continue

    def release_seed(self):
        if self.seed_count <= 0:
            return None
        self.seed_count -= 1
        return (self.x, self.y + self.radius + 14)

    def split_bubble(self):
        if self.bubble_count <= PLAYER_MIN_BUBBLES:
            self.bubble_count = 0
            self.burst = True
            return None
        self.bubble_count -= 1
        return (self.x, self.y - self.radius - 14)

    def touch_pollution(self, dt):
        self.pollution = min(POLLUTION_LIMIT, self.pollution + 28 * dt)

    def is_dead(self):
        return self.burst or self.bubble_count <= 0 or self.pollution >= POLLUTION_LIMIT

    def draw(self, screen):
        bubble_surface = pygame.Surface((self.radius * 2 + 8, self.radius * 2 + 8), pygame.SRCALPHA)
        center = (self.radius + 4, self.radius + 4)
        pollution_alpha = int(30 + self.pollution * 1.4)
        pygame.draw.circle(bubble_surface, (130, 221, 255, 70), center, self.radius)
        pygame.draw.circle(bubble_surface, (220, 249, 255, 180), center, self.radius, 3)
        if self.pollution > 0:
            pygame.draw.circle(bubble_surface, (130, 54, 150, pollution_alpha), center, max(8, self.radius - 5))

        if self.seed_count > 0:
            seed_radius = 6
            start_x = center[0] - (self.seed_count - 1) * 7
            for index in range(self.seed_count):
                pygame.draw.circle(bubble_surface, (142, 255, 177, 220), (start_x + index * 14, center[1]), seed_radius)
        pygame.draw.circle(bubble_surface, WHITE, (center[0] - self.radius // 3, center[1] - self.radius // 4), 4)
        screen.blit(bubble_surface, (self.x - self.radius - 4, self.y - self.radius - 4))
