import math

import pygame

from config import (
    BUBBLE_VENT_RADIUS,
    BUBBLE_VENT_SPAWN_INTERVAL,
    BURST_EFFECT_DURATION,
    ENERGY_COLOR,
    FREE_BUBBLE_RADIUS,
    LEAF_COLOR,
    LEAF_DARK,
    LEAF_GRAY,
    LEAF_YELLOW,
    POLLUTION_COLOR,
    SPIKE_COLOR,
    SPIKE_DARK,
    WALL_COLOR,
    WALL_EDGE,
    WHITE,
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

    def collides_with_circle(self, center, radius):
        cx, cy = center
        if cx + radius < self.rect.left or cx - radius > self.rect.right:
            return False
        if cy + radius < self.rect.top or cy - radius > self.rect.bottom:
            return False

        triangle = self.points
        if self.point_in_triangle(cx, cy, triangle):
            return True
        if any((cx - px) ** 2 + (cy - py) ** 2 <= radius * radius for px, py in triangle):
            return True
        for start, end in zip(triangle, triangle[1:] + triangle[:1]):
            if self.segment_intersects_circle(start, end, center, radius):
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

    @staticmethod
    def segment_intersects_circle(start, end, center, radius):
        sx, sy = start
        ex, ey = end
        cx, cy = center
        dx = ex - sx
        dy = ey - sy
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return (cx - sx) ** 2 + (cy - sy) ** 2 <= radius * radius
        t = ((cx - sx) * dx + (cy - sy) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        closest_x = sx + dx * t
        closest_y = sy + dy * t
        return (cx - closest_x) ** 2 + (cy - closest_y) ** 2 <= radius * radius

    def draw(self, screen):
        pygame.draw.polygon(screen, SPIKE_COLOR, self.points)
        pygame.draw.polygon(screen, SPIKE_DARK, self.points, 2)


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

    def collides_with_body(self, body):
        if not hasattr(body, "x") or not hasattr(body, "y") or not hasattr(body, "radius"):
            return self.rect.colliderect(body)
        radius = body.radius
        if not self.rect.inflate(radius * 2, radius * 2).collidepoint(body.x, body.y):
            return False
        return circle_collides_with_polygon((body.x, body.y), radius, leaf_outline_points(self.rect))

    def draw(self, screen):
        draw_leaf(screen, self.rect, self.color)


def draw_leaf(screen, rect, color):
    pad = 12
    leaf_surface = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    w = rect.width
    h = rect.height
    origin_x = pad
    origin_y = pad

    leaf_points = leaf_outline_points(pygame.Rect(origin_x, origin_y, w, h))

    base = color
    edge = blend_color(color, LEAF_DARK, 0.45)
    shade = blend_color(color, (2, 20, 28), 0.42)
    highlight = blend_color(color, WHITE, 0.38)
    inner = blend_color(color, WHITE, 0.14)

    shadow_rect = pygame.Rect(origin_x + w * 0.02, origin_y + h * 0.55, w * 0.88, h * 0.28)
    pygame.draw.ellipse(leaf_surface, (2, 18, 24, 62), shadow_rect)

    for scale, alpha in ((1.055, 18), (1.025, 28)):
        glow_points = scale_points(leaf_points, (origin_x + w * 0.5, origin_y + h * 0.48), scale)
        pygame.draw.polygon(leaf_surface, (*highlight, alpha), glow_points)

    pygame.draw.polygon(leaf_surface, (*shade, 225), [(x, y + 4) for x, y in leaf_points])
    pygame.draw.polygon(leaf_surface, (*base, 238), leaf_points)
    pygame.draw.polygon(leaf_surface, (*inner, 105), scale_points(leaf_points, (origin_x + w * 0.5, origin_y + h * 0.48), 0.82))
    pygame.draw.aalines(
        leaf_surface,
        (*highlight, 118),
        True,
        scale_points(leaf_points, (origin_x + w * 0.5, origin_y + h * 0.48), 1.008),
    )
    pygame.draw.aalines(leaf_surface, (*edge, 240), True, leaf_points)

    vein = cubic_points(
        (origin_x + w * 0.13, origin_y + h * 0.58),
        (origin_x + w * 0.36, origin_y + h * 0.50),
        (origin_x + w * 0.66, origin_y + h * 0.42),
        (origin_x + w * 0.91, origin_y + h * 0.37),
        18,
    )
    pygame.draw.lines(leaf_surface, (*edge, 150), False, [(x, y + 2) for x, y in vein], 3)
    pygame.draw.aalines(leaf_surface, (*highlight, 230), False, vein)

    side_veins = (
        (0.32, -0.18, 0.48, -0.02),
        (0.47, -0.12, 0.62, 0.00),
        (0.61, -0.08, 0.75, 0.01),
        (0.35, 0.15, 0.52, 0.08),
        (0.52, 0.16, 0.68, 0.07),
    )
    for start_t, end_dy, end_t, start_dy in side_veins:
        start = point_on_polyline(vein, start_t)
        end_x = origin_x + w * end_t
        end_y = start[1] + h * end_dy + h * start_dy
        pygame.draw.aaline(leaf_surface, (*highlight, 120), start, (end_x, end_y))

    pygame.draw.circle(leaf_surface, (255, 255, 255, 72), (int(origin_x + w * 0.31), int(origin_y + h * 0.22)), 4)
    pygame.draw.circle(leaf_surface, (255, 255, 255, 44), (int(origin_x + w * 0.39), int(origin_y + h * 0.18)), 2)

    screen.blit(leaf_surface, (rect.x - pad, rect.y - pad))


def leaf_outline_points(rect):
    w = rect.width
    h = rect.height
    stem = (rect.x + w * 0.08, rect.y + h * 0.58)
    tip = (rect.x + w * 0.94, rect.y + h * 0.36)
    top_controls = (
        (rect.x + w * 0.23, rect.y + h * -0.14),
        (rect.x + w * 0.76, rect.y + h * -0.02),
    )
    bottom_controls = (
        (rect.x + w * 0.78, rect.y + h * 0.88),
        (rect.x + w * 0.23, rect.y + h * 0.98),
    )
    top_edge = cubic_points(stem, top_controls[0], top_controls[1], tip, 16)
    bottom_edge = cubic_points(tip, bottom_controls[0], bottom_controls[1], stem, 16)
    return top_edge + bottom_edge


def cubic_points(p0, p1, p2, p3, steps):
    points = []
    for index in range(steps + 1):
        t = index / steps
        inv = 1 - t
        x = inv ** 3 * p0[0] + 3 * inv ** 2 * t * p1[0] + 3 * inv * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = inv ** 3 * p0[1] + 3 * inv ** 2 * t * p1[1] + 3 * inv * t ** 2 * p2[1] + t ** 3 * p3[1]
        points.append((x, y))
    return points


def scale_points(points, center, scale):
    return [
        (
            center[0] + (x - center[0]) * scale,
            center[1] + (y - center[1]) * scale,
        )
        for x, y in points
    ]


def point_on_polyline(points, t):
    index = max(0, min(len(points) - 1, int(t * (len(points) - 1))))
    return points[index]


def blend_color(first, second, amount):
    return tuple(
        int(first[index] + (second[index] - first[index]) * amount)
        for index in range(3)
    )


def circle_collides_with_polygon(center, radius, points):
    if point_in_polygon(center, points):
        return True
    radius_sq = radius * radius
    for start, end in zip(points, points[1:] + points[:1]):
        if distance_sq_to_segment(center, start, end) <= radius_sq:
            return True
    return False


def point_in_polygon(point, points):
    x, y = point
    inside = False
    previous = points[-1]
    for current in points:
        xi, yi = current
        xj, yj = previous
        crosses = (yi > y) != (yj > y)
        if crosses:
            x_at_y = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_at_y:
                inside = not inside
        previous = current
    return inside


def distance_sq_to_segment(point, start, end):
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        nearest_x, nearest_y = sx, sy
    else:
        t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_sq))
        nearest_x = sx + t * dx
        nearest_y = sy + t * dy
    offset_x = px - nearest_x
    offset_y = py - nearest_y
    return offset_x * offset_x + offset_y * offset_y
