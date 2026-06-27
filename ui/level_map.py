import math

import pygame

from config import MUTED_TEXT, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from levels.catalog import (
    DEFAULT_REGION,
    THORN_REEF_REGION,
    last_level_index,
    region_display_name,
)
from ui.widgets import (
    draw_liquid_glass_surface,
    draw_star,
    draw_wrapped_text,
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

    def draw(self, screen):
        self.draw_picture(screen)
        self.draw_route(screen)
        self.draw_nodes(screen)
        self.draw_region_gate(screen)
        self.draw_hover_panel(screen)
        self.draw_save_button(screen)
        self.draw_back_button(screen)

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
        beams = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        for x in (30, 360, 710):
            pygame.draw.polygon(
                beams,
                (160, 226, 248, 20),
                [
                    (x, 0),
                    (x + 94, 0),
                    (x + 198, SCREEN_HEIGHT),
                    (x + 62, SCREEN_HEIGHT),
                ],
            )
        screen.blit(beams, (0, 0))
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
            gate_color = (
                (247, 188, 63)
                if scene.latest_level_index
                >= last_level_index(DEFAULT_REGION)
                else (105, 116, 122)
            )
            self.draw_dotted_line(
                screen,
                centers[-1],
                self.region_gate_center(),
                gate_color,
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
            "解锁荆棘礁",
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
        if scene.level_hovered is None:
            return

        rect = self.hover_panel_rect()
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_liquid_glass_surface(
            panel,
            panel.get_rect(),
            selected=True,
        )

        if scene.level_hovered == "gate":
            title = scene.tab_font.render(
                "荆棘礁入口",
                True,
                WHITE,
            )
            panel.blit(title, (24, 28))
            status = f"消耗 {scene.unlock_seed_cost} 颗种子解锁"
            status_text = scene.small_font.render(
                status,
                True,
                (184, 236, 255),
            )
            panel.blit(status_text, (24, 58))
            description = (
                "连续释放四颗种子后，泡泡必须仍然存活，"
                "才能进入下一片海域。"
            )
            draw_wrapped_text(
                panel,
                description,
                pygame.Rect(24, 84, 270, 56),
                MUTED_TEXT,
                scene.small_font,
            )
        else:
            mini_rect = pygame.Rect(18, 24, 118, 92)
            self.draw_minimap(
                panel,
                mini_rect,
                scene.level_hovered,
            )

            label, _ = scene.all_level_tabs[scene.level_hovered]
            title = scene.tab_font.render(label, True, WHITE)
            panel.blit(title, (154, 28))

            locked = not scene.is_level_unlocked(scene.level_hovered)
            playable = scene.is_level_playable(scene.level_hovered)
            if locked:
                status = "未解锁"
                status_color = MUTED_TEXT
            elif not playable:
                status = "已离开海域"
                status_color = (190, 200, 205)
            else:
                status = "可进入"
                status_color = (184, 236, 255)
            status_text = scene.small_font.render(
                status,
                True,
                status_color,
            )
            panel.blit(status_text, (154, 58))

            stars = scene.level_star_count(scene.level_hovered)
            if stars is not None:
                for index in range(3):
                    filled = index < int(stars)
                    color = (
                        (255, 221, 126)
                        if filled
                        else (120, 115, 96)
                    )
                    draw_star(
                        panel,
                        (174 + index * 28, 84),
                        9,
                        color,
                        filled=filled,
                    )
                description_top = 102
            else:
                description_top = 84

            description = scene.all_level_descriptions[
                scene.level_hovered
            ]
            draw_wrapped_text(
                panel,
                description,
                pygame.Rect(154, description_top, 154, 56),
                MUTED_TEXT,
                scene.small_font,
            )
        screen.blit(panel, rect)

    def hover_panel_rect(self):
        panel_width = 334
        panel_height = 158
        margin = 24
        gap = 38
        center = self.hover_center()
        if center is None:
            return pygame.Rect(
                SCREEN_WIDTH - panel_width - margin,
                164,
                panel_width,
                panel_height,
            )

        x = center[0] + gap
        if x + panel_width + margin > SCREEN_WIDTH:
            x = center[0] - gap - panel_width
        x = max(
            margin,
            min(x, SCREEN_WIDTH - panel_width - margin),
        )
        y = center[1] - panel_height // 2
        y = max(
            134,
            min(y, SCREEN_HEIGHT - panel_height - 64),
        )
        return pygame.Rect(x, y, panel_width, panel_height)

    def hover_center(self):
        scene = self.scene
        if scene.level_hovered == "gate":
            return self.region_gate_center()
        if scene.level_hovered in scene.visible_level_indices:
            display_index = scene.visible_level_indices.index(
                scene.level_hovered
            )
            return self.node_centers()[display_index]
        return None

    def draw_minimap(self, surface, rect, level_index):
        draw_liquid_glass_surface(
            surface,
            rect,
            selected=False,
            radius=6,
        )
        water_line = rect.bottom - 18
        pygame.draw.line(
            surface,
            (77, 151, 168),
            (rect.left + 8, water_line),
            (rect.right - 8, water_line),
            2,
        )
        start = (rect.left + 18, rect.bottom - 28)
        goal = (rect.right - 20, rect.top + 24)
        pygame.draw.circle(surface, (83, 188, 126), start, 7)
        pygame.draw.circle(surface, (223, 193, 92), goal, 7)

        if level_index == 0:
            pygame.draw.arc(
                surface,
                (184, 236, 255),
                (rect.left + 24, rect.top + 20, 62, 48),
                0.15,
                2.8,
                3,
            )
            pygame.draw.circle(
                surface,
                (139, 244, 166),
                (rect.left + 64, rect.top + 36),
                4,
            )
        elif level_index == 1:
            pygame.draw.line(
                surface,
                (184, 236, 255),
                (rect.left + 22, rect.top + 58),
                (rect.right - 28, rect.top + 42),
                3,
            )
            pygame.draw.circle(
                surface,
                (238, 248, 255),
                (rect.left + 64, rect.top + 64),
                6,
                2,
            )
        else:
            pygame.draw.rect(
                surface,
                (28, 77, 86),
                (rect.left + 38, rect.top + 18, 12, 58),
                border_radius=3,
            )
            pygame.draw.rect(
                surface,
                (28, 77, 86),
                (rect.left + 70, rect.top + 44, 36, 10),
                border_radius=3,
            )
            for x in (
                rect.left + 58,
                rect.left + 78,
                rect.left + 98,
            ):
                pygame.draw.polygon(
                    surface,
                    (219, 228, 220),
                    [
                        (x, rect.top + 40),
                        (x + 6, rect.top + 54),
                        (x - 6, rect.top + 54),
                    ],
                )

    def back_rect(self):
        return pygame.Rect(
            SCREEN_WIDTH - 164,
            SCREEN_HEIGHT - 48,
            144,
            38,
        )

    def save_rect(self):
        return pygame.Rect(44, 38, 116, 42)

    def draw_back_button(self, screen):
        scene = self.scene
        rect = self.back_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_liquid_glass_surface(
            surface,
            surface.get_rect(),
            selected=False,
        )
        label = scene.tab_font.render("返回", True, WHITE)
        surface.blit(
            label,
            label.get_rect(center=surface.get_rect().center),
        )
        screen.blit(surface, rect)

    def draw_save_button(self, screen):
        scene = self.scene
        rect = self.save_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_liquid_glass_surface(
            surface,
            surface.get_rect(),
            selected=False,
        )
        label = scene.small_font.render("保存", True, WHITE)
        surface.blit(
            label,
            label.get_rect(center=surface.get_rect().center),
        )
        screen.blit(surface, rect)
