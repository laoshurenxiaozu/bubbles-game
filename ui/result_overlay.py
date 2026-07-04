import pygame

from config import (
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)
from levels.catalog import display_level_name
from ui.widgets import (
    ControlHintVisibility,
    draw_control_hints,
    draw_star,
)


RESULT_PANEL = pygame.Rect(220, 70, 520, 400)


class ResultOverlayView:
    def __init__(self, scene):
        self.scene = scene
        self.control_hint_visibility = ControlHintVisibility(
            enabled=lambda: scene.control_hints_enabled
        )

    def draw(self, screen):
        scene = self.scene
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 14, 24, 170))
        screen.blit(overlay, (0, 0))

        panel = RESULT_PANEL
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
        title = scene.big_font.render("关卡完成", True, WHITE)
        surface.blit(
            title,
            title.get_rect(center=(panel.width / 2, 48)),
        )

        stars = int(
            scene.stars_by_level.get(str(scene.level_index), 1)
        )
        for index in range(3):
            filled = index < stars
            color = (
                (255, 221, 126)
                if filled
                else (162, 144, 86)
            )
            draw_star(
                surface,
                (panel.width / 2 - 52 + index * 52, 120),
                18,
                color,
                filled=filled,
                outline_width=3,
            )

        if scene.result_mode == "summary":
            self.draw_summary(surface)
        elif scene.save_flow == "choose_action":
            self.draw_save_actions(surface)
        else:
            self.draw_save_slots(surface)

        if scene.save_message:
            message_surface = scene.font.render(
                scene.save_message,
                True,
                (255, 221, 126),
            )
            surface.blit(
                message_surface,
                message_surface.get_rect(
                    center=(panel.width / 2, panel.height - 8)
                ),
            )
        screen.blit(surface, panel.topleft)

    def draw_summary(self, surface):
        scene = self.scene
        for index, choice in enumerate(scene.result_actions):
            selected = index == scene.result_menu_index
            label = self.choice_label(choice)
            color = WHITE if selected else MUTED_TEXT
            option_surface = scene.big_font.render(
                label,
                True,
                color,
            )
            surface.blit(
                option_surface,
                option_surface.get_rect(
                    center=(RESULT_PANEL.width / 2, 210 + index * 42)
                ),
            )
        draw_control_hints(
            surface,
            (
                ("W/S", "选择"),
                ("Enter", "确认"),
                ("R", "重开"),
                ("M", "地图"),
            ),
            scene.small_font,
            (RESULT_PANEL.width / 2, 378),
            visibility=self.control_hint_visibility,
            context="result_summary",
            elapsed=scene.time,
            screen_offset=RESULT_PANEL.topleft,
        )

    def choice_label(self, choice):
        if (
            choice == "next"
            and self.scene.level_index == len(self.scene.levels) - 1
        ):
            return "最终检测"
        return {
            "next": "下一关",
            "restart": "重新开始",
            "save": "保存",
            "level_map": "退出",
        }.get(choice, choice)

    def draw_save_actions(self, surface):
        scene = self.scene
        header = scene.font.render("选择保存方式", True, TEXT_COLOR)
        surface.blit(header, (40, 188))
        for index, (label, _) in enumerate(
            scene.save_action_options()
        ):
            rect = self.local_save_action_rect(index)
            selected = index == scene.save_action_index
            fill = (
                (27, 92, 110, 220)
                if selected
                else (17, 63, 82, 200)
            )
            edge = (
                (208, 246, 255)
                if selected
                else (96, 148, 160)
            )
            pygame.draw.rect(
                surface,
                fill,
                rect,
                border_radius=12,
            )
            pygame.draw.rect(
                surface,
                edge,
                rect,
                2,
                border_radius=12,
            )
            option_surface = scene.font.render(
                label,
                True,
                WHITE if selected else TEXT_COLOR,
            )
            surface.blit(
                option_surface,
                option_surface.get_rect(center=rect.center),
            )
        draw_control_hints(
            surface,
            (
                ("W/S", "选择"),
                ("Enter", "确认"),
                ("Esc", "返回"),
            ),
            scene.small_font,
            (RESULT_PANEL.width / 2, 356),
            visibility=self.control_hint_visibility,
            context="result_save_actions",
            elapsed=scene.time,
            screen_offset=RESULT_PANEL.topleft,
        )

    def draw_save_slots(self, surface):
        scene = self.scene
        header_text = (
            "正在编辑名称，再按回车保存"
            if scene.save_editing
            else "选择另一个存档位，按回车编辑名称"
        )
        header = scene.font.render(header_text, True, TEXT_COLOR)
        surface.blit(header, (40, 180))
        for index in range(3):
            self.draw_save_slot(surface, index)

        current_name = (
            scene.save_name_input
            if scene.save_name_input
            else scene.default_save_name(scene.save_slot_index)
        )
        name_label = scene.font.render(
            f"存档名：{current_name}",
            True,
            WHITE,
        )
        surface.blit(name_label, (40, 372))

    def draw_save_slot(self, surface, index):
        scene = self.scene
        rect = self.local_save_slot_rect(index)
        locked = scene.current_save_slot_locked(index)
        selected = index == scene.save_slot_index
        if locked:
            fill = (11, 40, 50, 168)
            edge = (88, 122, 132)
            text_color = MUTED_TEXT
        else:
            fill = (
                (27, 92, 110, 220)
                if selected
                else (17, 63, 82, 200)
            )
            edge = (
                (208, 246, 255)
                if selected
                else (96, 148, 160)
            )
            text_color = WHITE

        pygame.draw.rect(
            surface,
            fill,
            rect,
            border_radius=10,
        )
        pygame.draw.rect(
            surface,
            edge,
            rect,
            2,
            border_radius=10,
        )
        slot_name, level_name, seed_total = scene.save_slot_summary(
            index
        )
        prefix_surface = scene.font.render(
            f"存档 {index + 1}: ",
            True,
            text_color,
        )
        surface.blit(
            prefix_surface,
            prefix_surface.get_rect(
                midleft=(rect.left + 12, rect.centery)
            ),
        )
        name_x = rect.left + 12 + prefix_surface.get_width()
        self.draw_save_slot_name(
            surface,
            slot_name,
            name_x,
            rect,
            fill,
            selected,
            text_color,
        )

        suffix_surface = scene.font.render(
            (
                f" | {display_level_name(level_name)}"
                f" | 种子 {seed_total}"
            ),
            True,
            text_color,
        )
        suffix_x = rect.right - 12 - suffix_surface.get_width()
        surface.blit(
            suffix_surface,
            suffix_surface.get_rect(
                midleft=(suffix_x, rect.centery)
            ),
        )

    def draw_save_slot_name(
        self,
        surface,
        slot_name,
        name_x,
        rect,
        fill,
        selected,
        text_color,
    ):
        scene = self.scene
        if selected and scene.save_editing:
            cursor_visible = int(scene.save_cursor_timer * 2) % 2 == 0
            name_surface = scene.font.render(
                scene.save_name_input,
                True,
                WHITE,
            )
            surface.blit(
                name_surface,
                name_surface.get_rect(
                    midleft=(name_x, rect.centery)
                ),
            )
            cursor_surface = scene.font.render(
                "_",
                True,
                WHITE if cursor_visible else fill,
            )
            cursor_x = name_x + name_surface.get_width()
            surface.blit(
                cursor_surface,
                cursor_surface.get_rect(
                    midleft=(cursor_x, rect.centery - 2)
                ),
            )
            return
        name_surface = scene.font.render(
            slot_name,
            True,
            text_color,
        )
        surface.blit(
            name_surface,
            name_surface.get_rect(
                midleft=(name_x, rect.centery)
            ),
        )

    def option_rect(self, index):
        width = 320
        height = 40
        left = RESULT_PANEL.left + (
            RESULT_PANEL.width - width
        ) // 2
        top = (
            RESULT_PANEL.top
            + 210
            + index * 42
            - height // 2
        )
        return pygame.Rect(left, top, width, height)

    def save_action_rect(self, index):
        return self.local_save_action_rect(index).move(
            RESULT_PANEL.left,
            RESULT_PANEL.top,
        )

    def save_slot_rect(self, index):
        return self.local_save_slot_rect(index).move(
            RESULT_PANEL.left,
            RESULT_PANEL.top,
        )

    def local_save_action_rect(self, index):
        return pygame.Rect(
            72,
            224 + index * 60,
            RESULT_PANEL.width - 144,
            42,
        )

    def local_save_slot_rect(self, index):
        return pygame.Rect(
            40,
            214 + index * 48,
            RESULT_PANEL.width - 80,
            38,
        )

    def option_at_pos(self, pos):
        for index in range(len(self.scene.result_actions)):
            if self.option_rect(index).collidepoint(pos):
                return index
        return None
