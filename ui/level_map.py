import math

import pygame

from config import MUTED_TEXT, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from levels.catalog import (
    DEFAULT_REGION,
    THORN_REEF_REGION,
    region_display_name,
)
from ui.widgets import (
    ControlHintVisibility,
    draw_control_hints,
    draw_star,
)


REGION_ROUTES = {
    DEFAULT_REGION: [
        (128, 388),
        (342, 302),
        (586, 370),
        (768, 288),
    ],
    THORN_REEF_REGION: [
        (148, 382),
        (354, 292),
        (594, 366),
        (812, 278),
    ],
}

HOVER_PANEL_WIDTH = 198
HOVER_PANEL_HEIGHT = 114


def level_node_centers(region, count):
    if count <= 0:
        return []
    if count == 1:
        return [(SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT // 2 + 36)]

    route = REGION_ROUTES.get(region, REGION_ROUTES[DEFAULT_REGION])
    if count == len(route):
        return list(route)

    centers = []
    for index in range(count):
        t = index / (count - 1)
        position = t * (len(route) - 1)
        left = min(int(position), len(route) - 2)
        local_t = position - left
        x1, y1 = route[left]
        x2, y2 = route[left + 1]
        centers.append(
            (
                int(x1 + (x2 - x1) * local_t),
                int(y1 + (y2 - y1) * local_t),
            )
        )
    return centers


class LevelMapView:
    def __init__(self, scene):
        self.scene = scene
        self.control_hint_visibility = ControlHintVisibility(
            enabled=lambda: scene.control_hints_enabled
        )

    def draw(self, screen):
        self.draw_picture(screen)
        self.draw_route(screen)
        self.draw_nodes(screen)
        self.draw_region_gate(screen)
        self.draw_hover_panel(screen)

        scene = self.scene
        title = scene.tab_font.render("关卡选择", True, (242, 252, 226))
        shadow = scene.tab_font.render("关卡选择", True, (11, 35, 55))
        shadow.set_alpha(125)
        screen.blit(
            shadow,
            shadow.get_rect(center=(SCREEN_WIDTH / 2 + 1, 57)),
        )
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 55)))

        subtitle_text = (
            scene.map_message or region_display_name(scene.viewed_region)
        )
        subtitle = scene.subtitle_font.render(
            subtitle_text,
            True,
            (199, 222, 230),
        )
        screen.blit(
            subtitle,
            subtitle.get_rect(center=(SCREEN_WIDTH / 2, 116)),
        )
        draw_control_hints(
            screen,
            (
                ("A/D", "选择"),
                ("Enter", "进入"),
                ("S", "保存"),
                ("Esc", "返回"),
            ),
            scene.small_font,
            (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 24),
            visibility=self.control_hint_visibility,
            context="level_map",
            elapsed=scene.time,
        )

    def node_centers(self):
        scene = self.scene
        return level_node_centers(
            scene.viewed_region,
            len(scene.visible_level_indices),
        )

    def node_at_pos(self, pos):
        scene = self.scene
        for index, center in enumerate(self.node_centers()):
            if math.dist(pos, center) <= 24:
                return scene.visible_level_indices[index]
        if scene.show_region_gate() and math.dist(
            pos,
            self.region_gate_center(),
        ) <= 28:
            return "gate"
        return None

    def draw_picture(self, screen):
        self.scene.draw_background(screen)
        depth = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        depth.fill((0, 18, 28, 34))
        screen.blit(depth, (0, 0))

    def draw_route(self, screen):
        scene = self.scene
        centers = self.node_centers()
        if len(centers) < 2:
            return

        for index, (start, end) in enumerate(
            zip(centers, centers[1:])
        ):
            start_level_index = scene.visible_level_indices[index]
            color = (
                (229, 72, 58)
                if start_level_index < scene.latest_level_index
                else (105, 116, 122)
            )
            self.draw_dotted_line(screen, start, end, color)
        if scene.show_region_gate() and centers:
            self.draw_dotted_line(
                screen,
                centers[-1],
                self.region_gate_center(),
                (247, 188, 63),
            )

    def draw_dotted_line(self, screen, start, end, color):
        distance = math.dist(start, end)
        if distance <= 0:
            return
        steps = max(1, int(distance / 22))
        for step in range(1, steps):
            t = step / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            pygame.draw.circle(
                screen,
                (12, 31, 44),
                (int(x), int(y)),
                8,
            )
            pygame.draw.circle(screen, color, (int(x), int(y)), 6)
            pygame.draw.circle(
                screen,
                (255, 238, 224, 170),
                (int(x - 2), int(y - 3)),
                2,
            )

    def draw_nodes(self, screen):
        scene = self.scene
        for display_index, center in enumerate(self.node_centers()):
            self.draw_node(
                screen,
                scene.visible_level_indices[display_index],
                center,
            )

    def region_gate_center(self):
        return (906, 190)

    def draw_selection_glow(self, screen, center):
        glow = pygame.Surface((66, 66), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (255, 240, 158, 66),
            (33, 33),
            30,
        )
        screen.blit(glow, (center[0] - 33, center[1] - 33))

    def draw_region_gate(self, screen):
        scene = self.scene
        if not scene.show_region_gate():
            return
        center = self.region_gate_center()
        selected = scene.level_selected == "gate"
        unlocked = scene.can_attempt_region_unlock()
        if selected:
            self.draw_selection_glow(screen, center)
        rim = (252, 252, 232) if selected else (230, 238, 230)
        fill = (247, 188, 63) if unlocked else (124, 137, 143)
        pygame.draw.circle(screen, (9, 28, 42), center, 22)
        pygame.draw.circle(screen, rim, center, 20)
        pygame.draw.circle(screen, fill, center, 17)
        lock_text = scene.small_font.render(
            str(scene.unlock_seed_cost),
            True,
            (9, 28, 42),
        )
        screen.blit(lock_text, lock_text.get_rect(center=center))
        label = scene.small_font.render(
            scene.unlock_gate_label(),
            True,
            WHITE if unlocked else MUTED_TEXT,
        )
        screen.blit(
            label,
            label.get_rect(center=(center[0], center[1] + 42)),
        )

    def draw_node(self, screen, index, center):
        scene = self.scene
        unlocked = scene.is_level_unlocked(index)
        playable = scene.is_level_playable(index)
        passed = index < scene.latest_level_index
        selected = index == scene.level_selected

        if selected and playable:
            self.draw_selection_glow(screen, center)

        rim = (
            (252, 252, 232)
            if selected and playable
            else (230, 238, 230)
        )
        fill = (230, 72, 62) if passed else (247, 188, 63)
        if not unlocked:
            fill = (124, 137, 143)
            rim = (177, 188, 192)
        elif not playable:
            fill = (92, 108, 116)
            rim = (160, 176, 182)

        pygame.draw.circle(screen, (9, 28, 42), center, 18)
        pygame.draw.circle(screen, rim, center, 16)
        pygame.draw.circle(screen, fill, center, 13)

        label, _ = scene.all_level_tabs[index]
        if not unlocked:
            label_color = (143, 159, 166)
        elif not playable:
            label_color = (164, 176, 182)
        else:
            label_color = (238, 246, 235)
        text = scene.tab_font.render(label, True, label_color)
        shadow = scene.tab_font.render(label, True, (8, 27, 39))
        shadow.set_alpha(130)
        label_y = center[1] + (34 if index == 1 else 38)
        screen.blit(
            shadow,
            shadow.get_rect(center=(center[0] + 1, label_y + 1)),
        )
        screen.blit(text, text.get_rect(center=(center[0], label_y)))

    def draw_hover_panel(self, screen):
        scene = self.scene
        inspected_item = scene.previewed_map_item()
        if not isinstance(inspected_item, int):
            return

        rect = self.hover_panel_rect()
        center = self.hover_center()
        accent = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        if center is not None:
            pygame.draw.line(
                accent,
                (206, 235, 242, 135),
                rect.midbottom,
                (center[0], center[1] - 22),
                1,
            )
        screen.blit(accent, (0, 0))

        shadow = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow,
            (0, 10, 18, 42),
            shadow.get_rect(),
            border_radius=9,
        )
        screen.blit(shadow, rect.move(0, 2))

        preview_rect = rect.inflate(-6, -6)
        underlay = screen.subsurface(preview_rect).copy()
        scene.draw_level_preview(
            screen,
            preview_rect,
            inspected_item,
        )
        self.restore_preview_corners(
            screen,
            preview_rect,
            underlay,
            radius=7,
        )
        self.draw_preview_stars(screen, rect, inspected_item)

        border = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            border,
            (220, 241, 246, 190),
            border.get_rect(),
            1,
            border_radius=9,
        )
        screen.blit(border, rect)

    def draw_preview_stars(self, screen, panel_rect, level_index):
        stars = int(
            self.scene.progress_data.get("stars_by_level", {}).get(
                str(level_index),
                0,
            )
        )
        stars = max(0, min(3, stars))

        bar = pygame.Rect(0, 0, 72, 22)
        bar.midbottom = (panel_rect.centerx, panel_rect.top - 4)

        for index in range(3):
            filled = index < stars
            color = (
                (255, 224, 132, 218)
                if filled
                else (206, 236, 240, 94)
            )
            draw_star(
                screen,
                (bar.left + 18 + index * 18, bar.centery),
                7,
                color,
                filled=filled,
                outline_width=1,
            )

    @staticmethod
    def restore_preview_corners(
        screen,
        rect,
        underlay,
        radius,
    ):
        for local_y in range(radius):
            for local_x in range(radius):
                dx = radius - local_x - 0.5
                dy = radius - local_y - 0.5
                if dx * dx + dy * dy <= radius * radius:
                    continue
                points = (
                    (local_x, local_y),
                    (rect.width - 1 - local_x, local_y),
                    (local_x, rect.height - 1 - local_y),
                    (
                        rect.width - 1 - local_x,
                        rect.height - 1 - local_y,
                    ),
                )
                for x, y in points:
                    screen.set_at(
                        (rect.left + x, rect.top + y),
                        underlay.get_at((x, y)),
                    )

    def hover_panel_rect(self):
        center = self.hover_center()
        if center is None:
            return pygame.Rect(
                24,
                140,
                HOVER_PANEL_WIDTH,
                HOVER_PANEL_HEIGHT,
            )

        margin = 24
        gap = 38
        x = center[0] - HOVER_PANEL_WIDTH // 2
        x = max(
            margin,
            min(x, SCREEN_WIDTH - HOVER_PANEL_WIDTH - margin),
        )
        y = center[1] - HOVER_PANEL_HEIGHT - gap
        y = max(
            134,
            min(y, SCREEN_HEIGHT - HOVER_PANEL_HEIGHT - 64),
        )
        return pygame.Rect(
            x,
            y,
            HOVER_PANEL_WIDTH,
            HOVER_PANEL_HEIGHT,
        )

    def hover_center(self):
        scene = self.scene
        inspected_item = scene.previewed_map_item()
        if inspected_item not in scene.visible_level_indices:
            return None
        display_index = scene.visible_level_indices.index(
            inspected_item
        )
        return self.node_centers()[display_index]
