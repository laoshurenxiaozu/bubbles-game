import math

import pygame

from config import (
    GOAL_COLOR,
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
)


def draw_star(surface, center, outer_radius, color, filled=True, outline_width=2):
    inner_radius = outer_radius * 0.46
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * (math.pi / 5)
        radius = outer_radius if index % 2 == 0 else inner_radius
        points.append(
            (
                center[0] + math.cos(angle) * radius,
                center[1] + math.sin(angle) * radius,
            )
        )
    if filled:
        pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, color, points, outline_width)


def draw_liquid_glass_surface(surface, rect, selected, radius=8):
    shadow = rect.move(0, 5)
    pygame.draw.rect(surface, (0, 0, 0, 36), shadow, border_radius=radius)

    fill_alpha = 28 if selected else 17
    edge_alpha = 218 if selected else 142
    pygame.draw.rect(
        surface,
        (255, 255, 255, fill_alpha),
        rect,
        border_radius=radius,
    )
    pygame.draw.rect(
        surface,
        (255, 255, 255, edge_alpha),
        rect,
        2,
        border_radius=radius,
    )
    pygame.draw.rect(
        surface,
        (255, 255, 255, 38),
        rect.inflate(-8, -8),
        1,
        border_radius=max(4, radius - 2),
    )

    highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(
        highlight,
        (255, 255, 255, 44 if selected else 28),
        (
            -rect.width * 0.2,
            -rect.height * 0.55,
            rect.width * 0.9,
            rect.height * 0.8,
        ),
    )
    pygame.draw.arc(
        highlight,
        (255, 255, 255, 86 if selected else 48),
        (12, 8, rect.width - 24, max(18, rect.height // 2)),
        math.radians(188),
        math.radians(350),
        2,
    )
    pygame.draw.arc(
        highlight,
        (255, 255, 255, 30),
        (
            rect.width // 2,
            rect.height // 3,
            rect.width // 2,
            rect.height // 2,
        ),
        math.radians(100),
        math.radians(235),
        2,
    )
    surface.blit(highlight, rect.topleft)

    if selected:
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            (255, 255, 255, 40),
            glow.get_rect().inflate(-10, -10),
            border_radius=max(4, radius - 2),
        )
        pygame.draw.line(
            glow,
            (255, 255, 255, 82),
            (18, 10),
            (rect.width - 18, 10),
            2,
        )
        pygame.draw.line(
            glow,
            (*GOAL_COLOR, 70),
            (18, rect.height - 9),
            (rect.width - 18, rect.height - 9),
            2,
        )
        surface.blit(glow, rect.topleft)


def draw_liquid_glass_panel(screen, rect, selected, radius=8):
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    draw_liquid_glass_surface(surface, surface.get_rect(), selected, radius)
    screen.blit(surface, rect)


def wrap_units(text):
    if " " not in text:
        return list(text)
    units = []
    for index, word in enumerate(text.split(" ")):
        if index:
            units.append(" ")
        units.append(word)
    return units


def draw_wrapped_text(surface, text, rect, color, font):
    line = ""
    y = rect.top
    for word in wrap_units(text):
        candidate = word if not line else f"{line}{word}"
        if font.size(candidate)[0] <= rect.width:
            line = candidate
            continue
        if line and word in "，。！？；：、）】》”’":
            line = candidate
            continue
        if line:
            surface.blit(font.render(line, True, color), (rect.left, y))
            y += font.get_linesize()
        line = word
        if y + font.get_linesize() > rect.bottom:
            return
    if line and y + font.get_linesize() <= rect.bottom:
        surface.blit(font.render(line, True, color), (rect.left, y))


def draw_status_overlay(screen, title, hint, title_font, hint_font):
    overlay = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.SRCALPHA,
    )
    overlay.fill((0, 14, 24, 150))
    screen.blit(overlay, (0, 0))

    title_surface = title_font.render(title, True, TEXT_COLOR)
    hint_surface = hint_font.render(hint, True, MUTED_TEXT)
    screen.blit(
        title_surface,
        title_surface.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20)
        ),
    )
    screen.blit(
        hint_surface,
        hint_surface.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
        ),
    )
