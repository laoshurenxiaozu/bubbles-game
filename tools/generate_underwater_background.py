import math
from pathlib import Path
import random

import pygame


WIDTH = 1920
HEIGHT = 1080
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "underwater_menu_bg.png"


def lerp(a, b, t):
    return int(a + (b - a) * t)


def draw_gradient(surface):
    top = (40, 142, 177)
    mid = (9, 88, 127)
    bottom = (2, 27, 58)
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        if t < 0.56:
            lt = t / 0.56
            color = tuple(lerp(top[i], mid[i], lt) for i in range(3))
        else:
            lt = (t - 0.56) / 0.44
            color = tuple(lerp(mid[i], bottom[i], lt) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))


def draw_light_shafts(surface):
    # Keep the background clean: animated caustics and particles provide
    # water movement in-game, while hard light shafts tend to fight the UI.
    return


def draw_caustics(surface):
    caustics = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    random.seed(42)
    for row in range(4):
        y = 96 + row * 82
        for x in range(-80, WIDTH + 80, 220):
            wobble = random.randint(-22, 22)
            rect = pygame.Rect(x + wobble, y, 150, 32)
            pygame.draw.arc(caustics, (218, 250, 255, 10), rect, 0.18, math.pi - 0.18, 2)
    surface.blit(caustics, (0, 0))


def draw_water_texture(surface):
    texture = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    random.seed(8)
    for _ in range(650):
        x = random.randint(0, WIDTH)
        y = random.randint(20, HEIGHT - 20)
        radius = random.choice([1, 1, 1, 2])
        alpha = random.randint(4, 16)
        pygame.draw.circle(texture, (218, 252, 255, alpha), (x, y), radius)

    for layer, alpha in [(0, 14), (1, 10), (2, 8)]:
        y_base = 250 + layer * 165
        points = []
        for x in range(-80, WIDTH + 100, 90):
            y = int(y_base + 22 * math.sin(x * 0.004 + layer) + 8 * math.sin(x * 0.015))
            points.append((x, y))
        pygame.draw.lines(texture, (135, 219, 234, alpha), False, points, 10 + layer * 3)
    surface.blit(texture, (0, 0))


def draw_depth_vignette(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for step in range(0, 420, 10):
        alpha = int(1 + (step / 420) ** 2 * 5)
        pygame.draw.rect(overlay, (0, 12, 30, alpha), (step, step // 3, WIDTH - step * 2, HEIGHT - step // 2), 4)
    pygame.draw.rect(overlay, (0, 12, 26, 24), (0, 0, WIDTH, HEIGHT))
    surface.blit(overlay, (0, 0))


def main():
    pygame.init()
    canvas = pygame.Surface((WIDTH, HEIGHT))
    draw_gradient(canvas)
    draw_light_shafts(canvas)
    draw_caustics(canvas)
    draw_water_texture(canvas)
    draw_depth_vignette(canvas)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, OUTPUT)
    pygame.quit()
    print(OUTPUT)


if __name__ == "__main__":
    main()
