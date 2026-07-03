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


class ControlHintVisibility:
    def __init__(
        self,
        duration=3.0,
        fade_duration=0.35,
        reentry_gap=0.75,
    ):
        self.duration = duration
        self.fade_duration = fade_duration
        self.reentry_gap = reentry_gap
        self.context = None
        self.started_at = 0.0
        self.last_seen_at = None

    def opacity(self, context, elapsed, hovered=False):
        reentered = (
            self.last_seen_at is not None
            and elapsed - self.last_seen_at > self.reentry_gap
        )
        if (
            context != self.context
            or elapsed < self.started_at
            or reentered
        ):
            self.context = context
            self.started_at = elapsed
        self.last_seen_at = elapsed
        if hovered:
            return 255

        age = elapsed - self.started_at
        if age <= self.duration:
            return 255
        if self.fade_duration <= 0:
            return 0
        fade_progress = min(
            1.0,
            (age - self.duration) / self.fade_duration,
        )
        return int(255 * (1.0 - fade_progress))


def draw_control_hints(
    surface,
    items,
    font,
    center,
    key_color=TEXT_COLOR,
    label_color=MUTED_TEXT,
    visibility=None,
    context=None,
    elapsed=0.0,
    screen_offset=(0, 0),
):
    """Draw a quiet row of keyboard hints without taking over the layout."""
    if not items:
        return pygame.Rect(center[0], center[1], 0, 0)

    key_height = max(22, font.get_height() + 6)
    item_gap = 18
    label_gap = 7
    measured = []
    content_width = 0

    for key, label in items:
        key_text = font.render(key, True, key_color)
        label_text = font.render(label, True, label_color)
        key_width = max(26, key_text.get_width() + 12)
        item_width = key_width + label_gap + label_text.get_width()
        measured.append(
            (key_text, label_text, key_width, item_width)
        )
        content_width += item_width
    content_width += item_gap * (len(items) - 1)

    group_size = (
        content_width,
        key_height,
    )
    group = pygame.Surface(group_size, pygame.SRCALPHA)

    x = 0
    for key_text, label_text, key_width, item_width in measured:
        key_rect = pygame.Rect(
            x,
            0,
            key_width,
            key_height,
        )
        pygame.draw.rect(
            group,
            (210, 241, 248, 12),
            key_rect,
            border_radius=6,
        )
        pygame.draw.rect(
            group,
            (210, 241, 248, 98),
            key_rect,
            1,
            border_radius=6,
        )
        group.blit(
            key_text,
            key_text.get_rect(center=key_rect.center),
        )
        group.blit(
            label_text,
            label_text.get_rect(
                midleft=(
                    key_rect.right + label_gap,
                    key_rect.centery,
                )
            ),
        )
        x += item_width + item_gap

    rect = group.get_rect(center=center)
    if visibility:
        hover_rect = rect.move(screen_offset).inflate(16, 12)
        alpha = visibility.opacity(
            context,
            elapsed,
            hover_rect.collidepoint(pygame.mouse.get_pos()),
        )
        if alpha <= 0:
            return rect
        group.set_alpha(alpha)
    surface.blit(group, rect)
    return rect


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
