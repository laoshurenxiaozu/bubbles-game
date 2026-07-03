import pygame

from config import (
    ENERGY_COLOR,
    GOAL_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from ui.menu_effects import draw_rising_bubbles, draw_underwater_gradient
from ui.widgets import ControlHintVisibility, draw_control_hints


class PauseMenuView:
    def __init__(self, scene):
        self.scene = scene
        self.control_hint_visibility = ControlHintVisibility()

    def draw(self, screen):
        scene = self.scene
        if scene.pause_mode == "settings":
            self.draw_settings(screen)
            return

        self.draw_background(screen)
        self.draw_title(screen)
        for index, (label, _) in enumerate(scene.pause_options()):
            rect = self.tab_rect(index)
            self.draw_glass_tab(
                screen,
                rect,
                label,
                index == scene.pause_menu_index,
            )

        draw_control_hints(
            screen,
            (
                ("W/S", "选择"),
                ("Enter", "确认"),
                ("Esc", "继续"),
            ),
            scene.font,
            (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34),
            visibility=self.control_hint_visibility,
            context="pause",
            elapsed=scene.time,
        )

    def draw_background(self, screen):
        scene = self.scene
        draw_underwater_gradient(screen)
        draw_rising_bubbles(screen, scene.menu_bubbles, scene.time)

    def draw_title(self, screen):
        scene = self.scene
        title = scene.title_font.render("暂停", True, WHITE)
        shadow = scene.title_font.render("暂停", True, (30, 95, 113))
        screen.blit(
            shadow,
            shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)),
        )
        screen.blit(
            title,
            title.get_rect(center=(SCREEN_WIDTH / 2, 78)),
        )
        subtitle = scene.font.render(
            "喘口气，再潜回深海",
            True,
            TEXT_COLOR,
        )
        screen.blit(
            subtitle,
            subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)),
        )

    def draw_settings(self, screen):
        scene = self.scene
        self.draw_background(screen)
        self.draw_settings_title(screen)
        self.draw_back_button(screen)

        heading = scene.font.render("设置", True, TEXT_COLOR)
        screen.blit(
            heading,
            heading.get_rect(center=(SCREEN_WIDTH / 2, 190)),
        )
        for index, (label, value) in enumerate(self.settings_rows()):
            rect = self.setting_rect(index)
            selected = index == scene.pause_settings_index
            self.draw_glass_panel(screen, rect, selected)
            color = WHITE if selected else TEXT_COLOR
            label_surface = scene.hint_font.render(
                label,
                True,
                color,
            )
            value_surface = scene.font.render(value, True, color)
            screen.blit(
                label_surface,
                label_surface.get_rect(
                    midleft=(rect.left + 18, rect.centery)
                ),
            )
            screen.blit(
                value_surface,
                value_surface.get_rect(
                    midright=(rect.right - 18, rect.centery)
                ),
            )

        draw_control_hints(
            screen,
            (
                ("W/S", "选择"),
                ("A/D", "调整"),
                ("Esc", "返回"),
            ),
            scene.font,
            (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34),
            visibility=self.control_hint_visibility,
            context="pause_settings",
            elapsed=scene.time,
        )

    def settings_rows(self):
        scene = self.scene
        return [
            ("音乐", f"{scene.music_volume}%"),
            ("音效", f"{scene.sfx_volume}%"),
            (
                "重开时显示提示动画",
                "开" if scene.restart_hint_enabled else "关",
            ),
        ]

    def draw_settings_title(self, screen):
        scene = self.scene
        title = scene.brand_font.render("Bubbles", True, WHITE)
        shadow = scene.brand_font.render(
            "Bubbles",
            True,
            (30, 95, 113),
        )
        screen.blit(
            shadow,
            shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)),
        )
        screen.blit(
            title,
            title.get_rect(center=(SCREEN_WIDTH / 2, 78)),
        )
        subtitle = scene.font.render(
            "携生命种子，从深海回到陆地",
            True,
            TEXT_COLOR,
        )
        screen.blit(
            subtitle,
            subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)),
        )

    def draw_back_button(self, screen):
        scene = self.scene
        rect = self.back_rect()
        self.draw_glass_panel(screen, rect, selected=False)
        label = scene.font.render("返回", True, TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_glass_tab(self, screen, rect, label, selected):
        scene = self.scene
        self.draw_glass_panel(screen, rect, selected)
        if selected:
            pygame.draw.circle(
                screen,
                ENERGY_COLOR,
                (rect.left + 28, rect.centery),
                5,
            )
        text = scene.big_font.render(
            label,
            True,
            WHITE if selected else TEXT_COLOR,
        )
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_glass_panel(self, screen, rect, selected):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill = (235, 250, 255, 48 if selected else 30)
        edge = (226, 250, 255, 210 if selected else 130)
        shine = (255, 255, 255, 54 if selected else 30)
        pygame.draw.rect(
            surface,
            fill,
            surface.get_rect(),
            border_radius=8,
        )
        pygame.draw.rect(
            surface,
            edge,
            surface.get_rect(),
            2,
            border_radius=8,
        )
        pygame.draw.line(
            surface,
            shine,
            (18, 10),
            (rect.width - 18, 10),
            2,
        )
        if selected:
            pygame.draw.rect(
                surface,
                (*GOAL_COLOR, 35),
                surface.get_rect().inflate(-8, -8),
                border_radius=6,
            )
        screen.blit(surface, rect)

    def back_rect(self):
        return pygame.Rect(44, 38, 116, 42)

    def setting_rect(self, index):
        return pygame.Rect(
            SCREEN_WIDTH / 2 - 190,
            236 + index * 58,
            380,
            46,
        )

    def tab_rect(self, index):
        width = 340
        height = 54
        gap = 14
        top = 190
        return pygame.Rect(
            (SCREEN_WIDTH - width) // 2,
            top + index * (height + gap),
            width,
            height,
        )

    def option_at_pos(self, pos):
        for index in range(len(self.scene.pause_options())):
            if self.tab_rect(index).collidepoint(pos):
                return index
        return None

    def setting_at_pos(self, pos):
        for index in range(len(self.settings_rows())):
            if self.setting_rect(index).collidepoint(pos):
                return index
        return None
