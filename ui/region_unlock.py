import pygame

from config import (
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from entities.objects import WildSeed
from ui.widgets import ControlHintVisibility, draw_control_hints


UNLOCK_LORE_HINT = "泡泡将承载生命种子，唤醒沉睡的海域"


class RegionUnlockView:
    def __init__(self, scene):
        self.scene = scene
        self.control_hint_visibility = ControlHintVisibility()

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
            lore = scene.small_font.render(
                UNLOCK_LORE_HINT,
                True,
                MUTED_TEXT,
            )
            surface.blit(
                lore,
                lore.get_rect(center=(panel.width / 2, 170)),
            )
            draw_control_hints(
                surface,
                (("Enter", "确认"), ("Esc", "取消")),
                scene.small_font,
                (panel.width / 2, 238),
                visibility=self.control_hint_visibility,
                context="unlock_confirm",
                elapsed=scene.time,
                screen_offset=panel.topleft,
            )
            hint = None
        else:
            if (
                scene.unlock_player
                and not (
                    scene.unlock_failed
                    and scene.mode in ("unlock_burst", "unlock_result")
                )
            ):
                scene.unlock_player.draw(surface)
            if scene.mode == "unlock_burst" and scene.unlock_burst_effect:
                scene.unlock_burst_effect.draw(surface)
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
        if hint is not None:
            surface.blit(
                hint,
                hint.get_rect(center=(panel.width / 2, 238)),
            )
        screen.blit(surface, panel.topleft)
