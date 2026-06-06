import math

import pygame

from config import (
    BUBBLE_VENT_RADIUS,
    BUBBLE_VENT_SPAWN_INTERVAL,
    BURST_EFFECT_DURATION,
    ENERGY_COLOR,
    FREE_BUBBLE_RADIUS,
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
        self.fusion_lock = 0.0

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
        self.radius = FREE_BUBBLE_RADIUS
        self.collected = False
        self.pickup_delay = pickup_delay
        self.fusion_lock = 0.0

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
        self.fusion_lock = max(0, self.fusion_lock - dt)
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
        self.collected = False
        self.fusion_lock = 0.0

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def draw(self, screen):
        pygame.draw.circle(screen, ENERGY_COLOR, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, (229, 255, 223), (self.x - 2, self.y - 2), 2)

class FusionBubble(FloatBody):
    def __init__(self, x, y, bubble_count=1, seed_count=1):
        super().__init__(x, y, bubble_count=bubble_count, seed_count=seed_count)
        self.radius = 9 + max(self.bubble_count, self.seed_count) * 2
        self.fusion_lock = 0.2
        self.collected = False

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def update(self, dt):
        previous_y = self.update_vertical_motion(dt)
        self.fusion_lock = max(0, self.fusion_lock - dt)
        self.radius = 9 + max(self.bubble_count, self.seed_count) * 2
        return previous_y

    def draw(self, screen):
        if self.collected:
            return
        inner_radius = max(10, self.radius - 4)
        bubble_surface = pygame.Surface((inner_radius * 2 + 8, inner_radius * 2 + 8), pygame.SRCALPHA)
        center = (inner_radius + 4, inner_radius + 4)
        pygame.draw.circle(bubble_surface, (130, 221, 255, 72), center, inner_radius)
        pygame.draw.circle(bubble_surface, (220, 249, 255, 195), center, inner_radius, 3)
        seed_radius = 4
        start_x = center[0] - (self.seed_count - 1) * 7
        for index in range(self.seed_count):
            pygame.draw.circle(
                bubble_surface,
                ENERGY_COLOR,
                (start_x + index * 14, center[1]),
                seed_radius,
            )
        pygame.draw.circle(bubble_surface, (229, 255, 223), (center[0] - inner_radius // 3, center[1] - inner_radius // 4), 2)
        screen.blit(bubble_surface, (self.x - inner_radius - 4, self.y - inner_radius - 4))


class BurstEffect:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.timer = BURST_EFFECT_DURATION

    @property
    def done(self):
        return self.timer <= 0

    def update(self, dt):
        self.timer = max(0, self.timer - dt)

    def draw(self, screen):
        if self.done:
            return
        progress = self.timer / BURST_EFFECT_DURATION
        ring_radius = int(self.radius + (1 - progress) * 18)
        alpha = int(190 * progress)
        ring_surface = pygame.Surface((ring_radius * 2 + 8, ring_radius * 2 + 8), pygame.SRCALPHA)
        center = (ring_radius + 4, ring_radius + 4)
        pygame.draw.circle(ring_surface, (220, 249, 255, alpha), center, ring_radius, 3)
        for dx, dy in ((-14, -8), (14, -10), (-10, 12), (12, 14)):
            pygame.draw.circle(
                ring_surface,
                (168, 231, 255, alpha),
                (center[0] + dx, center[1] + dy),
                max(2, int(4 * progress)),
            )
        screen.blit(ring_surface, (self.x - ring_radius - 4, self.y - ring_radius - 4))


class BubbleVent:
    def __init__(self, x, y, spawn_interval=BUBBLE_VENT_SPAWN_INTERVAL, radius=BUBBLE_VENT_RADIUS):
        self.x = x
        self.y = y
        self.spawn_interval = spawn_interval
        self.radius = radius
        self.timer = spawn_interval

    def update(self, dt):
        self.timer -= dt
        spawned = False
        while self.timer <= 0:
            self.timer += self.spawn_interval
            spawned = True
        return spawned

    def spawn_position(self):
        return self.x, self.y - self.radius - FREE_BUBBLE_RADIUS - 2

    def draw(self, screen):
        shell_rect = pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )
        pygame.draw.arc(screen, WALL_EDGE, shell_rect, 0, math.pi, 4)
        pygame.draw.arc(screen, WALL_COLOR, shell_rect.inflate(-8, -8), 0, math.pi, 4)
        pygame.draw.circle(screen, (205, 242, 255), (self.x - self.radius // 3, self.y - self.radius // 3), 3)

# Backwards-compatible name for older code paths.
InitialSeed = FusionBubble


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
        if not self.rect.colliderect(rect):
            return False

        triangle = self.points
        rect_points = [
            (rect.left, rect.top),
            (rect.right, rect.top),
            (rect.right, rect.bottom),
            (rect.left, rect.bottom),
        ]

        # Fast containment checks.
        if any(self.point_in_triangle(px, py, triangle) for px, py in rect_points):
            return True
        if any(rect.collidepoint(px, py) for px, py in triangle):
            return True

        # Edge intersection checks for cases where the triangle crosses the rect
        # without any corners landing inside the other shape.
        triangle_edges = list(zip(triangle, triangle[1:] + triangle[:1]))
        rect_edges = list(zip(rect_points, rect_points[1:] + rect_points[:1]))
        for tri_start, tri_end in triangle_edges:
            for rect_start, rect_end in rect_edges:
                if self.segments_intersect(tri_start, tri_end, rect_start, rect_end):
                    return True

        return False

    @staticmethod
    def point_in_triangle(px, py, triangle):
        (ax, ay), (bx, by), (cx, cy) = triangle
        denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if denom == 0:
            return False
        a = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / denom
        b = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / denom
        c = 1 - a - b
        return a >= 0 and b >= 0 and c >= 0

    @staticmethod
    def segments_intersect(p1, p2, p3, p4):
        def orientation(a, b, c):
            return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])

        def on_segment(a, b, c):
            return (
                min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
                and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
            )

        o1 = orientation(p1, p2, p3)
        o2 = orientation(p1, p2, p4)
        o3 = orientation(p3, p4, p1)
        o4 = orientation(p3, p4, p2)

        if o1 == 0 and on_segment(p1, p3, p2):
            return True
        if o2 == 0 and on_segment(p1, p4, p2):
            return True
        if o3 == 0 and on_segment(p3, p1, p4):
            return True
        if o4 == 0 and on_segment(p3, p2, p4):
            return True

        return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)

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
