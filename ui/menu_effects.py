import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH


DEFAULT_MENU_BUBBLES = (
    {"x": 86, "radius": 12, "duration": 4.8, "delay": 0.0, "drift": 12},
    {"x": 182, "radius": 20, "duration": 5.8, "delay": 1.2, "drift": 18},
    {"x": 342, "radius": 8, "duration": 4.2, "delay": 2.1, "drift": 10},
    {"x": 614, "radius": 16, "duration": 5.1, "delay": 0.7, "drift": 14},
    {"x": 806, "radius": 24, "duration": 6.4, "delay": 2.8, "drift": 20},
    {"x": 900, "radius": 10, "duration": 4.5, "delay": 1.7, "drift": 12},
    {"x": 468, "radius": 7, "duration": 3.9, "delay": 3.1, "drift": 8},
    {"x": 722, "radius": 13, "duration": 5.4, "delay": 3.8, "drift": 15},
)


def default_menu_bubbles():
    return [dict(bubble) for bubble in DEFAULT_MENU_BUBBLES]


def bubble_position_at_time(bubble, elapsed):
    progress = ((elapsed + bubble["delay"]) % bubble["duration"]) / bubble["duration"]
    x = bubble["x"] + math.sin(progress * math.tau * 1.4 + bubble["x"]) * bubble["drift"]
    y = SCREEN_HEIGHT + 42 - progress * (SCREEN_HEIGHT + 110)
    return (int(x), int(y))


def draw_underwater_gradient(screen):
    screen.fill((11, 49, 68))
    for y in range(SCREEN_HEIGHT):
        t = y / SCREEN_HEIGHT
        color = (
            int(11 + 8 * t),
            int(49 + 35 * t),
            int(68 + 46 * t),
        )
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))


def draw_rising_bubble(screen, bubble, elapsed):
    center = bubble_position_at_time(bubble, elapsed)
    progress = ((elapsed + bubble["delay"]) % bubble["duration"]) / bubble["duration"]
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


def draw_rising_bubbles(screen, bubbles, elapsed):
    for bubble in bubbles:
        draw_rising_bubble(screen, bubble, elapsed)

