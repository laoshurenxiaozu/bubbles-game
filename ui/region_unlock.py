import pygame

from config import (
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from entities.objects import WildSeed


class RegionUnlockView:
    def __init__(self, scene):
        self.scene = scene

    def draw(self, screen):
        scene = self.scene
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 14, 24, 180))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(170, 132, 620, 280)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(
            surface,
            (14, 55, 76, 238),
            surface.get_rect(),
            border_radius=26,
        )
        pygame.draw.rect(
            surface,
            (189, 231, 240),
            surface.get_rect(),
            3,
            border_radius=26,
        )
        title = scene.tab_font.render(
            "解锁荆棘礁",
            True,
            WHITE,
        )
        surface.blit(
            title,
            title.get_rect(center=(panel.width / 2, 40)),
        )

        if scene.mode == "unlock_confirm":
            body = scene.subtitle_font.render(
                scene.unlock_confirmation,
                True,
                TEXT_COLOR,
            )
            surface.blit(
                body,
                body.get_rect(center=(panel.width / 2, 112)),
            )
            hint = scene.small_font.render(
                "回车确认，Esc 取消",
                True,
                MUTED_TEXT,
            )
        else:
            if scene.unlock_player:
                scene.unlock_player.draw(surface)
            for seed in scene.unlock_emitted:
                WildSeed(seed.x, seed.y).draw(surface)
            hint_text = (
                f"正在献出 {scene.unlock_seed_cost} 颗种子泡泡，"
                "穿越礁门……"
                if scene.mode == "unlock_anim"
                else scene.unlock_status_message
            )
            hint_color = (
                TEXT_COLOR
                if scene.mode == "unlock_anim"
                else (255, 221, 126)
            )
            hint = scene.small_font.render(
                hint_text,
                True,
                hint_color,
            )
        surface.blit(
            hint,
            hint.get_rect(center=(panel.width / 2, 238)),
        )
        screen.blit(surface, panel.topleft)
