import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE


class LevelIntroView:
    def __init__(self, scene):
        self.scene = scene

    def draw(self, screen):
        scene = self.scene
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 12, 20, 120))
        screen.blit(overlay, (0, 0))

        prompt_font = scene.make_font(42)
        title_surface = prompt_font.render("按", True, WHITE)
        pulse = 1.0 + 0.06 * math.sin(scene.intro_time * 6.0)
        key_size = int(58 * pulse)
        d_key_surface = self.draw_key_surface(
            "D",
            key_size,
            pulse,
        )
        right_key_surface = self.draw_key_surface(
            "right",
            key_size,
            pulse,
        )
        slash_surface = prompt_font.render("/", True, WHITE)
        hint_surface = prompt_font.render("开始", True, WHITE)
        block_width = (
            title_surface.get_width()
            + d_key_surface.get_width()
            + slash_surface.get_width()
            + right_key_surface.get_width()
            + hint_surface.get_width()
            + 46
        )
        base_y = SCREEN_HEIGHT / 2
        x = SCREEN_WIDTH / 2 - block_width / 2
        screen.blit(
            title_surface,
            title_surface.get_rect(midleft=(x, base_y)),
        )
        x += title_surface.get_width() + 12
        screen.blit(
            d_key_surface,
            d_key_surface.get_rect(
                center=(
                    x + d_key_surface.get_width() / 2,
                    base_y + 2,
                )
            ),
        )
        x += d_key_surface.get_width() + 12
        screen.blit(
            slash_surface,
            slash_surface.get_rect(midleft=(x, base_y)),
        )
        x += slash_surface.get_width() + 12
        screen.blit(
            right_key_surface,
            right_key_surface.get_rect(
                center=(
                    x + right_key_surface.get_width() / 2,
                    base_y + 2,
                )
            ),
        )
        x += right_key_surface.get_width() + 14
        screen.blit(
            hint_surface,
            hint_surface.get_rect(midleft=(x, base_y)),
        )

    def draw_key_surface(self, label, key_size, pulse):
        scene = self.scene
        key_surface = pygame.Surface(
            (key_size, key_size),
            pygame.SRCALPHA,
        )
        rect = key_surface.get_rect()
        radius = max(12, int(key_size * 0.22))
        pygame.draw.rect(
            key_surface,
            (255, 255, 255, 22),
            rect,
            border_radius=radius,
        )
        pygame.draw.rect(
            key_surface,
            (255, 255, 255, 245),
            rect,
            3,
            border_radius=radius,
        )
        if label == "right":
            self.draw_right_arrow(key_surface, rect, pulse)
            return key_surface
        key_font = scene.make_font(32 * pulse)
        key_text = key_font.render(label, True, WHITE)
        key_surface.blit(
            key_text,
            key_text.get_rect(center=rect.center),
        )
        return key_surface

    def draw_right_arrow(self, surface, rect, pulse):
        center_y = rect.centery
        left = rect.left + int(rect.width * 0.30)
        right = rect.right - int(rect.width * 0.28)
        stroke = max(3, int(4 * pulse))
        pygame.draw.line(
            surface,
            WHITE,
            (left, center_y),
            (right, center_y),
            stroke,
        )
        arrow_size = int(rect.width * 0.16)
        pygame.draw.polygon(
            surface,
            WHITE,
            [
                (right + int(rect.width * 0.02), center_y),
                (right - arrow_size, center_y - arrow_size),
                (right - arrow_size, center_y + arrow_size),
            ],
        )
