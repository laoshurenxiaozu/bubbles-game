import math
from pathlib import Path

import pygame


WIDTH = 960
HEIGHT = 540
OUTPUT = Path(__file__).with_name("map_menu_mock.png")


def draw_vertical_gradient(surface, top_color, bottom_color):
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(
            int(top_color[i] + (bottom_color[i] - top_color[i]) * t)
            for i in range(3)
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


def draw_glow(surface, center, radius, color, alpha):
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for step in range(radius, 0, -6):
        strength = alpha * (step / radius) ** 2
        pygame.draw.circle(
            glow,
            (*color, int(strength)),
            (radius, radius),
            step,
        )
    surface.blit(glow, (center[0] - radius, center[1] - radius))


def draw_bubble_panel(surface, rect):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    cx = rect.width // 2
    cy = rect.height // 2
    radius = min(rect.width, rect.height) // 2 - 16

    draw_glow(panel, (cx, cy + 12), radius + 28, (85, 214, 255), 46)
    pygame.draw.circle(panel, (170, 233, 255, 36), (cx, cy), radius + 6)
    pygame.draw.circle(panel, (216, 248, 255, 130), (cx, cy), radius + 6, 3)
    pygame.draw.circle(panel, (244, 252, 255, 42), (cx, cy), radius - 18)

    square_size = 72
    gap = 18
    total_width = square_size * 3 + gap * 2
    start_x = cx - total_width // 2
    top_y = cy - square_size // 2 + 10

    font = pygame.font.Font(None, 52)
    for index in range(3):
        square_rect = pygame.Rect(
            start_x + index * (square_size + gap),
            top_y,
            square_size,
            square_size,
        )
        fill = (248, 251, 255, 228) if index == 0 else (220, 242, 248, 208)
        border = (255, 255, 255) if index == 0 else (191, 234, 246)
        pygame.draw.rect(panel, fill, square_rect, border_radius=18)
        pygame.draw.rect(panel, border, square_rect, 3, border_radius=18)

        text = font.render(str(index + 1), True, (17, 76, 98))
        panel.blit(text, text.get_rect(center=square_rect.center))

    highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(
        highlight,
        (255, 255, 255, 80),
        (cx - radius * 0.7, cy - radius * 0.95, radius * 0.85, radius * 0.42),
    )
    panel.blit(highlight, (0, 0))

    surface.blit(panel, rect.topleft)


def draw_caption(surface):
    title_font = pygame.font.Font(None, 74)
    subtitle_font = pygame.font.Font(None, 30)

    title = title_font.render("Bubble Map", True, (237, 249, 255))
    subtitle = subtitle_font.render("Level Select Concept", True, (173, 213, 226))

    surface.blit(title, title.get_rect(center=(WIDTH // 2, 84)))
    surface.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 124)))


def draw_water_details(surface):
    for x in range(0, WIDTH, 56):
        y = 418 + int(8 * math.sin(x / 48))
        pygame.draw.arc(
            surface,
            (87, 176, 196),
            (x, y, 52, 18),
            math.pi,
            math.tau,
            2,
        )

    for center, radius in [((138, 146), 10), ((178, 112), 6), ((792, 154), 8), ((840, 116), 12)]:
        pygame.draw.circle(surface, (180, 232, 245), center, radius, 2)


def main():
    pygame.init()
    pygame.font.init()

    canvas = pygame.Surface((WIDTH, HEIGHT))
    draw_vertical_gradient(canvas, (10, 61, 83), (18, 109, 126))
    draw_glow(canvas, (WIDTH // 2, HEIGHT // 2 + 30), 220, (82, 216, 255), 30)
    draw_water_details(canvas)
    draw_caption(canvas)
    draw_bubble_panel(canvas, pygame.Rect(250, 150, 460, 280))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(canvas, OUTPUT)
    pygame.quit()
    print(OUTPUT)


if __name__ == "__main__":
    main()
