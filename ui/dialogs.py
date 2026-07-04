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
    draw_liquid_glass_surface,
)


CONFIRM_PANEL = pygame.Rect(190, 150, 580, 210)
SAVE_PANEL = pygame.Rect(220, 70, 520, 400)


class ConfirmationDialogView:
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

        panel = CONFIRM_PANEL
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
            "进度未保存",
            True,
            WHITE,
        )
        save_available = scene.confirm_save_available()
        body_text = (
            "当前进度尚未保存。继续前要保存吗？"
            if save_available
            else scene.confirm_message
        )
        body = scene.small_font.render(
            body_text,
            True,
            TEXT_COLOR,
        )
        surface.blit(
            title,
            title.get_rect(center=(panel.width / 2, 46)),
        )
        surface.blit(
            body,
            body.get_rect(center=(panel.width / 2, 96)),
        )
        hint_items = (
            (
                ("A/D", "选择"),
                ("Enter", "确认"),
                ("Esc", "取消"),
            )
            if save_available
            else (("Enter", "继续"), ("Esc", "取消"))
        )
        draw_control_hints(
            surface,
            hint_items,
            scene.small_font,
            (panel.width / 2, 128),
            visibility=self.control_hint_visibility,
            context=("confirmation", save_available),
            elapsed=scene.time,
            screen_offset=panel.topleft,
        )

        if save_available:
            self.draw_button(
                surface,
                self.local_no_rect(),
                "不保存",
                scene.confirm_selected == "no",
            )
            self.draw_button(
                surface,
                self.local_yes_rect(),
                "保存",
                scene.confirm_selected == "yes",
            )
        else:
            self.draw_button(
                surface,
                self.local_no_rect(),
                "取消",
                False,
            )
            self.draw_button(
                surface,
                self.local_yes_rect(),
                "继续",
                True,
            )
        self.draw_close_button(surface)
        screen.blit(surface, panel.topleft)

    def draw_close_button(self, surface):
        scene = self.scene
        rect = self.local_close_rect()
        pygame.draw.circle(
            surface,
            (208, 246, 255),
            rect.center,
            11,
            2,
        )
        text = scene.small_font.render("x", True, TEXT_COLOR)
        surface.blit(
            text,
            text.get_rect(
                center=(rect.centerx, rect.centery - 1)
            ),
        )

    def draw_button(self, surface, rect, label, selected):
        scene = self.scene
        button = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_liquid_glass_surface(
            button,
            button.get_rect(),
            selected=selected,
            radius=10,
        )
        text = scene.small_font.render(
            label,
            True,
            WHITE if selected else TEXT_COLOR,
        )
        button.blit(
            text,
            text.get_rect(center=button.get_rect().center),
        )
        surface.blit(button, rect)

    def no_rect(self):
        return self.local_no_rect().move(
            CONFIRM_PANEL.left,
            CONFIRM_PANEL.top,
        )

    def yes_rect(self):
        return self.local_yes_rect().move(
            CONFIRM_PANEL.left,
            CONFIRM_PANEL.top,
        )

    def close_rect(self):
        return self.local_close_rect().move(
            CONFIRM_PANEL.left,
            CONFIRM_PANEL.top,
        )

    def local_no_rect(self):
        return pygame.Rect(110, 154, 144, 38)

    def local_yes_rect(self):
        return pygame.Rect(326, 154, 144, 38)

    def local_close_rect(self):
        return pygame.Rect(CONFIRM_PANEL.width - 42, 22, 24, 24)


class SaveDialogView:
    def __init__(self, scene):
        self.scene = scene
        self.title_font = scene.make_font(34)
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

        panel = SAVE_PANEL
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
        title = self.title_font.render("保存进度", True, WHITE)
        surface.blit(
            title,
            title.get_rect(center=(panel.width / 2, 48)),
        )

        if scene.save_flow == "choose_action":
            self.draw_actions(surface)
        else:
            self.draw_slots(surface)

        if scene.save_message:
            message_surface = scene.small_font.render(
                scene.save_message,
                True,
                (255, 221, 126),
            )
            surface.blit(
                message_surface,
                message_surface.get_rect(
                    center=(panel.width / 2, panel.height - 18)
                ),
            )
        screen.blit(surface, panel.topleft)

    def draw_actions(self, surface):
        scene = self.scene
        header = scene.small_font.render(
            "选择保存方式",
            True,
            TEXT_COLOR,
        )
        surface.blit(header, (40, 124))
        for index, (label, _) in enumerate(
            scene.save_action_options()
        ):
            rect = self.local_action_rect(index)
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
            option_surface = scene.small_font.render(
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
            (SAVE_PANEL.width / 2, 344),
            visibility=self.control_hint_visibility,
            context="save_actions",
            elapsed=scene.time,
            screen_offset=SAVE_PANEL.topleft,
        )

    def draw_slots(self, surface):
        scene = self.scene
        header_text = (
            "正在编辑名称，再按回车保存"
            if scene.save_editing
            else "选择另一个存档位，按回车编辑名称"
        )
        header = scene.small_font.render(
            header_text,
            True,
            TEXT_COLOR,
        )
        surface.blit(header, (40, 116))
        for index in range(3):
            self.draw_slot(surface, index)

        current_name = (
            scene.save_name_input
            if scene.save_name_input
            else scene.default_save_name(scene.save_slot_index)
        )
        name_label = scene.small_font.render(
            f"存档名：{current_name}",
            True,
            WHITE,
        )
        surface.blit(name_label, (40, 322))
        hint_items = (
            (
                ("Enter", "保存"),
                ("Backspace", "删除"),
                ("Esc", "取消"),
            )
            if scene.save_editing
            else (
                ("W/S", "选择"),
                ("Enter", "编辑"),
                ("Esc", "返回"),
            )
        )
        draw_control_hints(
            surface,
            hint_items,
            scene.small_font,
            (SAVE_PANEL.width / 2, 352),
            visibility=self.control_hint_visibility,
            context=("save_slots", scene.save_editing),
            elapsed=scene.time,
            screen_offset=SAVE_PANEL.topleft,
        )

    def draw_slot(self, surface, index):
        scene = self.scene
        rect = self.local_slot_rect(index)
        locked = scene.current_slot_locked(index)
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

        slot_name, level_name, seed_total = scene.load_slot_summary(
            index
        )
        prefix_surface = scene.small_font.render(
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
        if selected and scene.save_editing:
            cursor_visible = int(scene.save_cursor_timer * 2) % 2 == 0
            name_surface = scene.small_font.render(
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
            cursor_surface = scene.small_font.render(
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
        else:
            name_surface = scene.small_font.render(
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

        suffix_surface = scene.small_font.render(
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

    def action_rect(self, index):
        return self.local_action_rect(index).move(
            SAVE_PANEL.left,
            SAVE_PANEL.top,
        )

    def slot_rect(self, index):
        return self.local_slot_rect(index).move(
            SAVE_PANEL.left,
            SAVE_PANEL.top,
        )

    def local_action_rect(self, index):
        return pygame.Rect(
            72,
            164 + index * 60,
            SAVE_PANEL.width - 144,
            42,
        )

    def local_slot_rect(self, index):
        return pygame.Rect(
            40,
            154 + index * 48,
            SAVE_PANEL.width - 80,
            38,
        )
