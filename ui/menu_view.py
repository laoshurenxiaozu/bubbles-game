import pygame

from config import (
    ENERGY_COLOR,
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from levels.catalog import display_level_name
from ui.menu_effects import draw_rising_bubbles, draw_underwater_gradient
from ui.widgets import (
    draw_liquid_glass_panel,
    draw_liquid_glass_surface,
)


class MenuView:
    def __init__(self, scene):
        self.scene = scene

    def draw_background(self, screen):
        scene = self.scene
        if scene.background_image:
            screen.blit(scene.background_image, (0, 0))
            water_tint = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.SRCALPHA,
            )
            water_tint.fill((0, 24, 34, 42))
            screen.blit(water_tint, (0, 0))
        else:
            draw_underwater_gradient(screen)
        draw_rising_bubbles(screen, scene.bubbles, scene.time)

    def draw_title(self, screen):
        scene = self.scene
        title = scene.title_font.render("Bubbles", True, WHITE)
        shadow = scene.title_font.render(
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
        subtitle = scene.subtitle_font.render(
            "携生命种子，从深海回到陆地",
            True,
            TEXT_COLOR,
        )
        screen.blit(
            subtitle,
            subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)),
        )

    def draw_main(self, screen):
        scene = self.scene
        for index, (label, _) in enumerate(scene.main_tabs):
            rect = self.main_tab_rect(index)
            self.draw_glass_tab(
                screen,
                rect,
                label,
                index == scene.selected,
            )
        hint_text = (
            scene.load_message
            or "方向键或 W/S 选择，回车确认"
        )
        hint = scene.small_font.render(
            hint_text,
            True,
            MUTED_TEXT,
        )
        screen.blit(
            hint,
            hint.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)
            ),
        )

    def draw_load(self, screen):
        scene = self.scene
        self.draw_background(screen)
        self.draw_title(screen)
        heading = scene.subtitle_font.render(
            "读取存档",
            True,
            TEXT_COLOR,
        )
        screen.blit(
            heading,
            heading.get_rect(center=(SCREEN_WIDTH / 2, 190)),
        )

        for index in range(3):
            rect = self.load_slot_rect(index)
            selected = index == scene.load_selected
            draw_liquid_glass_panel(screen, rect, selected)
            name, level_name, seed_total = scene.load_slot_summary(
                index
            )
            title = scene.tab_font.render(
                f"存档 {index + 1}: {name}",
                True,
                WHITE if selected else TEXT_COLOR,
            )
            meta = scene.small_font.render(
                (
                    f"{display_level_name(level_name)}"
                    f"  |  种子 {seed_total}"
                ),
                True,
                WHITE if selected else MUTED_TEXT,
            )
            screen.blit(
                title,
                title.get_rect(
                    midleft=(rect.left + 20, rect.centery - 12)
                ),
            )
            screen.blit(
                meta,
                meta.get_rect(
                    midleft=(rect.left + 20, rect.centery + 14)
                ),
            )

        self.draw_load_back_button(screen)
        hint_text = (
            scene.load_message
            or "选择一个存档，读取后进入关卡地图"
        )
        hint = scene.small_font.render(
            hint_text,
            True,
            MUTED_TEXT,
        )
        screen.blit(
            hint,
            hint.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)
            ),
        )

    def draw_settings(self, screen):
        scene = self.scene
        self.draw_back_button(screen)
        heading = scene.subtitle_font.render(
            "设置",
            True,
            TEXT_COLOR,
        )
        screen.blit(
            heading,
            heading.get_rect(center=(SCREEN_WIDTH / 2, 190)),
        )

        for index, (label, value) in enumerate(
            scene.settings_rows()
        ):
            rect = self.setting_rect(index)
            selected = index == scene.settings_index
            draw_liquid_glass_panel(screen, rect, selected)
            color = WHITE if selected else TEXT_COLOR
            label_surface = scene.settings_font.render(
                label,
                True,
                color,
            )
            value_surface = scene.small_font.render(
                value,
                True,
                color,
            )
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

        hint = scene.small_font.render(
            "上下选择，左右调整",
            True,
            MUTED_TEXT,
        )
        screen.blit(
            hint,
            hint.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)
            ),
        )

    def draw_back_button(self, screen):
        scene = self.scene
        rect = self.back_rect()
        draw_liquid_glass_panel(screen, rect, selected=False)
        label = scene.small_font.render("返回", True, TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_load_back_button(self, screen):
        scene = self.scene
        rect = self.load_back_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            surface,
            (178, 210, 220, 62),
            surface.get_rect(),
            border_radius=8,
        )
        pygame.draw.rect(
            surface,
            (230, 246, 250, 190),
            surface.get_rect(),
            2,
            border_radius=8,
        )
        pygame.draw.rect(
            surface,
            (52, 82, 98, 170),
            surface.get_rect().inflate(-10, -8),
            border_radius=6,
        )
        label = scene.tab_font.render("返回", True, WHITE)
        surface.blit(
            label,
            label.get_rect(center=surface.get_rect().center),
        )
        screen.blit(surface, rect)

    def draw_glass_tab(self, screen, rect, label, selected):
        scene = self.scene
        draw_liquid_glass_panel(screen, rect, selected)
        if selected:
            pygame.draw.circle(
                screen,
                ENERGY_COLOR,
                (rect.left + 28, rect.centery),
                5,
            )
        text = scene.tab_font.render(
            label,
            True,
            WHITE if selected else TEXT_COLOR,
        )
        screen.blit(text, text.get_rect(center=rect.center))

    def main_tab_rect(self, index):
        width = 340
        height = 54
        gap = 12
        top = 166
        return pygame.Rect(
            (SCREEN_WIDTH - width) // 2,
            top + index * (height + gap),
            width,
            height,
        )

    def setting_rect(self, index):
        return pygame.Rect(
            SCREEN_WIDTH / 2 - 210,
            236 + index * 58,
            420,
            46,
        )

    def setting_at_pos(self, pos):
        for index in range(self.scene.settings_count()):
            if self.setting_rect(index).collidepoint(pos):
                return index
        return None

    def back_rect(self):
        return pygame.Rect(44, 38, 116, 42)

    def load_back_rect(self):
        return pygame.Rect(
            SCREEN_WIDTH - 164,
            SCREEN_HEIGHT - 48,
            144,
            38,
        )

    def load_slot_rect(self, index):
        return pygame.Rect(230, 240 + index * 86, 500, 62)

    def draw_liquid_glass_surface(
        self,
        surface,
        rect,
        selected,
        radius=8,
    ):
        return draw_liquid_glass_surface(
            surface,
            rect,
            selected,
            radius,
        )
