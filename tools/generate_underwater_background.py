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
    top = (13, 73, 95)
    mid = (6, 102, 119)
    bottom = (6, 37, 50)
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
    beams = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for x, width, alpha in [
        (-80, 260, 28),
        (430, 210, 22),
        (960, 300, 25),
        (1450, 220, 18),
    ]:
        pygame.draw.polygon(
            beams,
            (226, 251, 255, alpha),
            [
                (x, 0),
                (x + width, 0),
                (x + width + 260, HEIGHT),
                (x - 70, HEIGHT),
            ],
        )
    surface.blit(beams, (0, 0))


def draw_caustics(surface):
    caustics = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    random.seed(42)
    for row in range(8):
        y = 110 + row * 74
        for x in range(-80, WIDTH + 80, 160):
            wobble = random.randint(-22, 22)
            rect = pygame.Rect(x + wobble, y, 130, 38)
            pygame.draw.arc(caustics, (214, 251, 255, 18), rect, 0.18, math.pi - 0.18, 2)
    surface.blit(caustics, (0, 0))


def draw_water_texture(surface):
    texture = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    random.seed(8)
    for _ in range(420):
        x = random.randint(0, WIDTH)
        y = random.randint(40, HEIGHT - 80)
        radius = random.choice([1, 1, 2, 2, 3])
        alpha = random.randint(8, 26)
        pygame.draw.circle(texture, (218, 252, 255, alpha), (x, y), radius)

    for layer, alpha in [(0, 28), (1, 20), (2, 16)]:
        y_base = 610 + layer * 62
        points = []
        for x in range(-80, WIDTH + 100, 70):
            y = int(y_base + 28 * math.sin(x * 0.005 + layer) + 12 * math.sin(x * 0.017))
            points.append((x, y))
        pygame.draw.lines(texture, (21, 92, 96, alpha), False, points, 18 + layer * 6)
    surface.blit(texture, (0, 0))


def draw_seafloor(surface):
    floor = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    points = [(0, HEIGHT)]
    for x in range(0, WIDTH + 80, 80):
        y = int(776 + 40 * math.sin(x * 0.006) + 22 * math.sin(x * 0.019))
        points.append((x, y))
    points.append((WIDTH, HEIGHT))
    pygame.draw.polygon(floor, (13, 50, 43, 242), points)
    pygame.draw.polygon(floor, (33, 84, 59, 178), [(0, 840), (WIDTH, 804), (WIDTH, HEIGHT), (0, HEIGHT)])

    random.seed(18)
    for _ in range(90):
        x = random.randint(0, WIDTH)
        base = random.randint(790, 1040)
        height = random.randint(62, 190)
        sway = random.uniform(-0.32, 0.32)
        color = random.choice([(57, 151, 119, 168), (37, 124, 133, 152), (83, 169, 107, 142)])
        pts = []
        for step in range(5):
            f = step / 4
            pts.append((x + int(math.sin(f * math.pi) * height * sway), base - int(height * f)))
        pygame.draw.lines(floor, color, False, pts, random.randint(3, 7))

    for _ in range(44):
        x = random.randint(0, WIDTH)
        y = random.randint(782, 948)
        radius = random.randint(22, 64)
        color = random.choice([(156, 82, 104, 142), (212, 133, 91, 124), (73, 157, 139, 132), (190, 172, 105, 108)])
        pygame.draw.circle(floor, (0, 20, 24, 60), (x + 8, y + 10), radius)
        pygame.draw.circle(floor, color, (x, y), radius)
        pygame.draw.circle(floor, (239, 241, 217, 74), (x - radius // 3, y - radius // 3), max(3, radius // 8), 2)

    for x in (110, 260, 1560, 1730):
        for branch in range(7):
            angle = -math.pi / 2 + (branch - 3) * 0.22
            length = 74 + branch * 9
            start = (x, 870)
            end = (int(x + math.cos(angle) * length), int(870 + math.sin(angle) * length))
            pygame.draw.line(floor, (209, 119, 94, 138), start, end, 7)
            pygame.draw.circle(floor, (239, 178, 125, 120), end, 9)

    surface.blit(floor, (0, 0))


def draw_depth_vignette(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for step in range(0, 360, 8):
        alpha = int(1 + (step / 360) ** 2 * 6)
        pygame.draw.rect(overlay, (0, 14, 24, alpha), (step, step // 2, WIDTH - step * 2, HEIGHT - step), 4)
    pygame.draw.rect(overlay, (0, 15, 23, 34), (0, 0, WIDTH, HEIGHT))
    pygame.draw.rect(overlay, (0, 0, 0, 18), (0, 0, WIDTH, HEIGHT))
    surface.blit(overlay, (0, 0))


def main():
    pygame.init()
    canvas = pygame.Surface((WIDTH, HEIGHT))
    draw_gradient(canvas)
    draw_light_shafts(canvas)
    draw_caustics(canvas)
    draw_water_texture(canvas)
    draw_seafloor(canvas)
    draw_depth_vignette(canvas)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, OUTPUT)
    pygame.quit()
    print(OUTPUT)


if __name__ == "__main__":
    main()
