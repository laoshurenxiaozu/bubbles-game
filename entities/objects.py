import pygame

from config import (
    ENERGY_COLOR,
    GOAL_COLOR,
    LEAF_COLOR,
    LEAF_DARK,
    LEAF_GRAY,
    LEAF_YELLOW,
    POLLUTION_COLOR,
    SPIKE_COLOR,
    SPIKE_DARK,
    WALL_COLOR,
    WALL_EDGE,
)
from core.physics import FloatBody


class WildSeed(FloatBody):
    def __init__(self, x, y):
        super().__init__(x, y, bubble_count=1, seed_count=1)
        self.radius = 10
        self.collected = False

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def draw(self, screen):
        if self.collected:
            return
        pygame.draw.circle(screen, (168, 231, 255), (self.x, self.y), self.radius + 8, 2)
        pygame.draw.circle(screen, ENERGY_COLOR, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, (229, 255, 223), (self.x - 3, self.y - 3), 3)


class FreeBubble(FloatBody):
    def __init__(self, x, y, pickup_delay=0):
        super().__init__(x, y, bubble_count=1, seed_count=0)
        self.radius = 13
        self.collected = False
        self.pickup_delay = pickup_delay

    @property
    def can_pick_up(self):
        return self.pickup_delay <= 0

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def update(self, dt):
        previous_y = self.update_vertical_motion(dt)
        self.pickup_delay = max(0, self.pickup_delay - dt)
        return previous_y

    def draw(self, screen):
        if self.collected:
            return
        pygame.draw.circle(screen, (168, 231, 255), (self.x, self.y), self.radius, 2)
        pygame.draw.circle(screen, (234, 252, 255), (self.x - 4, self.y - 4), 3)


class DroppedSeed(FloatBody):
    def __init__(self, x, y):
        super().__init__(x, y, bubble_count=0, seed_count=1)
        self.radius = 8

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def draw(self, screen):
        pygame.draw.circle(screen, ENERGY_COLOR, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, (229, 255, 223), (self.x - 2, self.y - 2), 2)


class PollutionZone:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, screen):
        zone = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        zone.fill((*POLLUTION_COLOR, 125))
        pygame.draw.rect(zone, (173, 73, 177, 150), zone.get_rect(), 2, border_radius=8)
        screen.blit(zone, self.rect)


class Wall:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, screen):
        pygame.draw.rect(screen, WALL_COLOR, self.rect, border_radius=8)
        pygame.draw.rect(screen, WALL_EDGE, self.rect, 2, border_radius=8)
        for x in range(self.rect.left + 14, self.rect.right, 34):
            pygame.draw.circle(screen, (38, 93, 101), (x, self.rect.top + 10), 3)


class Spike:
    def __init__(self, x, y, width=34, height=28, direction="down"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.direction = direction
        self.rect = pygame.Rect(x, y, width, height)

    @property
    def points(self):
        if self.direction == "down":
            return [
                (self.x, self.y),
                (self.x + self.width, self.y),
                (self.x + self.width / 2, self.y + self.height),
            ]
        if self.direction == "up":
            return [
                (self.x, self.y + self.height),
                (self.x + self.width, self.y + self.height),
                (self.x + self.width / 2, self.y),
            ]
        if self.direction == "right":
            return [
                (self.x, self.y),
                (self.x, self.y + self.height),
                (self.x + self.width, self.y + self.height / 2),
            ]
        return [
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height / 2),
        ]

    def collides_with(self, rect):
        return self.rect.colliderect(rect)

    def draw(self, screen):
        pygame.draw.polygon(screen, SPIKE_COLOR, self.points)
        pygame.draw.polygon(screen, SPIKE_DARK, self.points, 2)


class Goal:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, screen):
        draw_leaf(screen, self.rect, GOAL_COLOR)


class Leaf:
    def __init__(self, rect, state="gray"):
        self.rect = pygame.Rect(rect)
        self.state = state

    @property
    def color(self):
        if self.state == "green":
            return LEAF_COLOR
        if self.state == "yellow":
            return LEAF_YELLOW
        return LEAF_GRAY

    def activate(self):
        self.state = "green"

    def draw(self, screen):
        draw_leaf(screen, self.rect, self.color)


def draw_leaf(screen, rect, color):
    leaf_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(leaf_surface, (*color, 210), leaf_surface.get_rect())
    pygame.draw.ellipse(leaf_surface, (*LEAF_DARK, 220), leaf_surface.get_rect(), 2)
    pygame.draw.line(
        leaf_surface,
        (*LEAF_DARK, 190),
        (rect.width * 0.18, rect.height * 0.55),
        (rect.width * 0.84, rect.height * 0.42),
        2,
    )
    pygame.draw.circle(leaf_surface, (226, 255, 220, 120), (int(rect.width * 0.32), int(rect.height * 0.32)), 4)
    screen.blit(leaf_surface, rect)
