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
            if self.resolve_swept_wall_face(wall.rect, radius):
                continue
            if self.circle_intersects_rect(wall.rect, radius):
                self.resolve_circle_rect_collision(wall.rect, radius)

    def resolve_swept_wall_face(self, rect, radius):
        prev_left = self.previous_x - radius
        prev_right = self.previous_x + radius
        prev_top = self.previous_y - radius
        prev_bottom = self.previous_y + radius
        curr_left = self.x - radius
        curr_right = self.x + radius
        curr_top = self.y - radius
        curr_bottom = self.y + radius

        if rect.left <= self.x <= rect.right:
            if prev_bottom <= rect.top and curr_bottom > rect.top:
                self.y = rect.top - radius
                return True
            if prev_top >= rect.bottom and curr_top < rect.bottom:
                self.y = rect.bottom + radius
                return True
        if rect.top <= self.y <= rect.bottom:
            if prev_right <= rect.left and curr_right > rect.left:
                self.x = rect.left - radius
                return True
            if prev_left >= rect.right and curr_left < rect.right:
                self.x = rect.right + radius
                return True
        return False

    def circle_intersects_rect(self, rect, radius):
        closest_x = max(rect.left, min(self.x, rect.right))
        closest_y = max(rect.top, min(self.y, rect.bottom))
        dx = self.x - closest_x
        dy = self.y - closest_y
        return dx * dx + dy * dy <= radius * radius

    def resolve_circle_rect_collision(self, rect, radius):
        closest_x = max(rect.left, min(self.x, rect.right))
        closest_y = max(rect.top, min(self.y, rect.bottom))
        dx = self.x - closest_x
        dy = self.y - closest_y
        distance_sq = dx * dx + dy * dy

        if distance_sq > 0:
            if dx and dy:
                distance = distance_sq ** 0.5
                push = radius - distance
                if push > 0:
                    self.x += dx / distance * push
                    self.y += dy / distance * push
                return
            if dx > 0:
                self.x = rect.right + radius
            elif dx < 0:
                self.x = rect.left - radius
            elif dy > 0:
                self.y = rect.bottom + radius
            elif dy < 0:
                self.y = rect.top - radius
            return

        candidates = []
        if self.previous_y + radius <= rect.top:
            candidates.append((abs(self.y - (rect.top - radius)), "y", rect.top - radius))
        if self.previous_y - radius >= rect.bottom:
            candidates.append((abs(self.y - (rect.bottom + radius)), "y", rect.bottom + radius))
        if self.previous_x + radius <= rect.left:
            candidates.append((abs(self.x - (rect.left - radius)), "x", rect.left - radius))
        if self.previous_x - radius >= rect.right:
            candidates.append((abs(self.x - (rect.right + radius)), "x", rect.right + radius))
        candidates.extend(
            (
                (abs(self.x - (rect.left - radius)), "x", rect.left - radius),
                (abs(self.x - (rect.right + radius)), "x", rect.right + radius),
                (abs(self.y - (rect.top - radius)), "y", rect.top - radius),
                (abs(self.y - (rect.bottom + radius)), "y", rect.bottom + radius),
            )
        )
        _, axis, value = min(candidates, key=lambda item: item[0])
        if axis == "x":
            self.x = value
        else:
            self.y = value

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
