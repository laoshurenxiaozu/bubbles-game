import math
from pathlib import Path

import pygame

from config import (
    ENERGY_COLOR,
    GOAL_COLOR,
    MUTED_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_COLOR,
    WHITE,
)


BACKGROUND_PATH = Path(__file__).resolve().parents[1] / "assets" / "underwater_menu_bg.png"


class MenuScene:
    def __init__(self, save_manager=None, progress_data=None):
        self.save_manager = save_manager
        self.progress_data = progress_data or {}
        self.title_font = self.make_font(82)
        self.subtitle_font = self.make_font(24)
        self.tab_font = self.make_font(30)
        self.small_font = self.make_font(18)
        self.mode = self.progress_data.get("open_mode", "main")
        self.selected = 0
        self.level_selected = 0
        self.load_selected = 0
        self.level_hovered = None
        self.load_message = self.progress_data.get("load_message", "")
        self.map_message = self.progress_data.get("map_message", "")
        self.time = 0.0
        self.music_volume = 80
        self.sfx_volume = 80
        self.background_image = self.load_background_image()
        self.bubbles = [
            (86, 108, 16, 0.9),
            (182, 422, 24, 1.2),
            (342, 148, 10, 1.6),
            (614, 96, 20, 1.0),
            (806, 386, 28, 1.4),
            (900, 170, 12, 1.8),
        ]
        self.main_tabs = [
            ("Start Game", "start"),
            ("Continue", "continue"),
            ("Load Game", "load"),
            ("Settings", "settings"),
            ("Quit", "quit"),
        ]
        self.level_tabs = [
            ("Tutorial 1", 0),
            ("Tutorial 2", 1),
            ("Tutorial 3", 2),
            ("Tutorial 4", 3),
        ]
        self.level_descriptions = [
            "Learn the first bubble movement route and reach the safe leaf.",
            "Practice seed release and collect the free bubble in open water.",
            "Navigate walls and spikes while managing buoyancy with split bubbles.",
            "Route fresh bubbles from the vent while preserving enough seeds to finish strong.",
        ]
        self.refresh_progress_state()

    def make_font(self, size):
        return pygame.font.Font(None, int(size))

    def refresh_progress_state(self):
        self.main_tabs = self.build_main_tabs()
        self.latest_level_index = min(
            self.progress_data.get("unlocked_levels", 0),
            len(self.level_tabs) - 1,
        )
        self.level_selected = min(
            self.progress_data.get("current_level_index", 0),
            self.latest_level_index,
        )
        self.selected = min(self.selected, len(self.main_tabs) - 1)

    def build_main_tabs(self):
        has_current_progress = bool(self.progress_data)
        start_label = "Restart" if has_current_progress else "Start Game"
        if has_current_progress:
            tabs = [("Continue", "continue"), (start_label, "start")]
        else:
            tabs = [(start_label, "start")]
        tabs.extend(
            [
                ("Load Game", "load"),
                ("Settings", "settings"),
                ("Quit", "quit"),
            ]
        )
        return tabs

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                action = self.handle_key(event.key)
                if action:
                    return action
            elif event.type == pygame.MOUSEMOTION:
                self.update_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self.handle_click(event.pos)
                if action:
                    return action
        return None

    def handle_key(self, key):
        if self.mode == "main":
            if key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.main_tabs)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.main_tabs)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_main_tab(self.selected)
        elif self.mode == "levels":
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "main"
                self.map_message = ""
            elif key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                self.level_selected = (self.level_selected - 1) % (self.latest_level_index + 1)
            elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                self.level_selected = (self.level_selected + 1) % (self.latest_level_index + 1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_level_node(self.level_selected)
        elif self.mode == "load":
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "main"
                self.load_message = ""
            elif key in (pygame.K_UP, pygame.K_w):
                self.load_selected = (self.load_selected - 1) % 3
                self.load_message = ""
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.load_selected = (self.load_selected + 1) % 3
                self.load_message = ""
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_load_slot(self.load_selected)
        elif self.mode == "settings":
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "main"
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.music_volume = max(0, self.music_volume - 10)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.music_volume = min(100, self.music_volume + 10)
        return None

    def activate_main_tab(self, index):
        action = self.main_tabs[index][1]
        if action == "start":
            self.progress_data = {}
            self.refresh_progress_state()
            self.mode = "levels"
            self.map_message = ""
            return None
        if action == "continue":
            if not self.progress_data:
                self.load_message = "No current run to continue"
                return None
            self.refresh_progress_state()
            self.mode = "levels"
            self.map_message = ""
            return None
        if action == "load":
            self.mode = "load"
            self.load_message = ""
        elif action == "settings":
            self.mode = "settings"
        elif action == "quit":
            return {"type": "quit"}
        return None

    def update_hover(self, pos):
        if self.mode == "levels":
            level_index = self.level_node_at_pos(pos)
            self.level_hovered = level_index
            if level_index is not None and self.is_level_unlocked(level_index):
                self.level_selected = level_index
            return
        if self.mode == "load":
            self.level_hovered = None
            for index in range(3):
                if self.load_slot_rect(index).collidepoint(pos):
                    self.load_selected = index
                    return

        self.level_hovered = None

        tabs = self.current_tab_rects()
        for index, rect in enumerate(tabs):
            if rect.collidepoint(pos):
                if self.mode == "main":
                    self.selected = index
                return

    def handle_click(self, pos):
        if self.mode == "levels":
            if self.level_back_rect().collidepoint(pos):
                self.mode = "main"
                self.map_message = ""
                return None
            return self.activate_level_node(self.level_node_at_pos(pos))
        if self.mode == "load":
            if self.load_back_rect().collidepoint(pos):
                self.mode = "main"
                self.load_message = ""
                return None
            for index in range(3):
                if self.load_slot_rect(index).collidepoint(pos):
                    self.load_selected = index
                    return self.activate_load_slot(index)
            return None

        tabs = self.current_tab_rects()
        for index, rect in enumerate(tabs):
            if rect.collidepoint(pos):
                if self.mode == "main":
                    self.selected = index
                    return self.activate_main_tab(index)

        if self.mode in ("levels", "settings"):
            back_rect = pygame.Rect(44, 38, 116, 42)
            if back_rect.collidepoint(pos):
                self.mode = "main"
        return None

    def activate_level_node(self, level_index):
        if level_index is None or not self.is_level_unlocked(level_index):
            return None
        self.level_selected = level_index
        return {
            "type": "start",
            "level": self.level_tabs[level_index][1],
            "slot_index": self.progress_data.get("slot_index"),
            "save_data": self.progress_data or None,
        }

    def activate_load_slot(self, slot_index):
        if not self.save_manager:
            self.load_message = "Save system unavailable"
            return None
        slot = self.save_manager.get_slot(slot_index)
        if not slot:
            self.load_message = f"Slot {slot_index + 1} is empty"
            return None
        self.progress_data = slot
        self.progress_data["slot_index"] = slot_index
        self.refresh_progress_state()
        self.mode = "levels"
        self.load_message = ""
        self.map_message = ""
        return None

    def is_level_unlocked(self, level_index):
        return level_index <= self.latest_level_index

    def level_node_centers(self):
        count = len(self.level_tabs)
        if count <= 1:
            return [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]

        route = [
            (128, 388),
            (342, 302),
            (586, 370),
            (768, 288),
            (854, 174),
        ]
        if count <= len(route):
            return route[:count]

        centers = []
        for index in range(count):
            t = index / (count - 1)
            position = t * (len(route) - 1)
            left = min(int(position), len(route) - 2)
            local_t = position - left
            x1, y1 = route[left]
            x2, y2 = route[left + 1]
            centers.append((
                int(x1 + (x2 - x1) * local_t),
                int(y1 + (y2 - y1) * local_t),
            ))
        return centers

    def level_node_at_pos(self, pos):
        for index, center in enumerate(self.level_node_centers()):
            if math.dist(pos, center) <= 24:
                return index
        return None

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        if self.mode == "levels":
            self.draw_levels(screen)
            return
        if self.mode == "load":
            self.draw_load(screen)
            return

        self.draw_background(screen)
        self.draw_title(screen)
        if self.mode == "main":
            self.draw_main(screen)
        else:
            self.draw_settings(screen)

    def draw_background(self, screen):
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
            water_tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            water_tint.fill((0, 24, 34, 42))
            screen.blit(water_tint, (0, 0))
        else:
            screen.fill((11, 49, 68))
            for y in range(SCREEN_HEIGHT):
                t = y / SCREEN_HEIGHT
                color = (
                    int(11 + 8 * t),
                    int(49 + 35 * t),
                    int(68 + 46 * t),
                )
                pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

        for x, y, radius, speed in self.bubbles:
            bob = math.sin(self.time * speed + x) * 10
            drift = math.cos(self.time * speed * 0.7 + y) * 8
            center = (int(x + drift), int(y + bob))
            pygame.draw.circle(screen, (184, 236, 255), center, radius, 2)
            pygame.draw.circle(screen, (238, 253, 255), (center[0] - radius // 3, center[1] - radius // 3), 3)

    def draw_title(self, screen):
        title = self.title_font.render("Bubbles", True, WHITE)
        shadow = self.title_font.render("Bubbles", True, (30, 95, 113))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 4, 82)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 78)))

        subtitle = self.subtitle_font.render("Carry the life seed from deep sea to land", True, TEXT_COLOR)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 132)))

    def draw_main(self, screen):
        for index, (label, _) in enumerate(self.main_tabs):
            rect = self.main_tab_rect(index)
            self.draw_glass_tab(screen, rect, label, index == self.selected)

        hint_text = "Use arrows or W/S, Enter to choose"
        if self.load_message:
            hint_text = self.load_message
        hint = self.small_font.render(hint_text, True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_levels(self, screen):
        self.draw_level_map_picture(screen)
        self.draw_level_map_route(screen)
        self.draw_level_map_nodes(screen)
        self.draw_level_hover_panel(screen)
        self.draw_level_map_back_button(screen)

        title = self.title_font.render("Level Map", True, (242, 252, 226))
        shadow = self.title_font.render("Level Map", True, (11, 35, 55))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 3, 59)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 55)))

        subtitle_text = self.map_message or "Unlocked levels can be replayed"
        subtitle = self.subtitle_font.render(subtitle_text, True, (199, 222, 230))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, 116)))

    def draw_load(self, screen):
        self.draw_background(screen)
        self.draw_title(screen)
        heading = self.subtitle_font.render("Load Game", True, TEXT_COLOR)
        screen.blit(heading, heading.get_rect(center=(SCREEN_WIDTH / 2, 190)))

        for index in range(3):
            rect = self.load_slot_rect(index)
            selected = index == self.load_selected
            self.draw_glass_panel(screen, rect, selected)
            name, level_name, seed_total = self.load_slot_summary(index)
            title = self.tab_font.render(f"Slot {index + 1}: {name}", True, WHITE if selected else TEXT_COLOR)
            meta = self.small_font.render(f"{level_name}  |  Seeds {seed_total}", True, WHITE if selected else MUTED_TEXT)
            screen.blit(title, title.get_rect(midleft=(rect.left + 20, rect.centery - 12)))
            screen.blit(meta, meta.get_rect(midleft=(rect.left + 20, rect.centery + 14)))

        self.draw_load_back_button(screen)
        hint_text = self.load_message or "Choose a slot to load, then jump to the level map"
        hint = self.small_font.render(hint_text, True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_level_map_picture(self, screen):
        self.draw_background(screen)

        beams = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in (30, 360, 710):
            pygame.draw.polygon(
                beams,
                (160, 226, 248, 20),
                [(x, 0), (x + 94, 0), (x + 198, SCREEN_HEIGHT), (x + 62, SCREEN_HEIGHT)],
            )
        screen.blit(beams, (0, 0))
        depth = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        depth.fill((0, 18, 28, 34))
        screen.blit(depth, (0, 0))

    def draw_level_map_route(self, screen):
        centers = self.level_node_centers()
        if len(centers) < 2:
            return

        for index, (start, end) in enumerate(zip(centers, centers[1:])):
            color = (229, 72, 58) if index < self.latest_level_index else (105, 116, 122)
            self.draw_dotted_line(screen, start, end, color)

    def draw_dotted_line(self, screen, start, end, color):
        distance = math.dist(start, end)
        if distance <= 0:
            return
        steps = max(1, int(distance / 22))
        for step in range(1, steps):
            t = step / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            pygame.draw.circle(screen, (12, 31, 44), (int(x), int(y)), 8)
            pygame.draw.circle(screen, color, (int(x), int(y)), 6)
            pygame.draw.circle(screen, (255, 238, 224, 170), (int(x - 2), int(y - 3)), 2)

    def draw_level_map_nodes(self, screen):
        for index, center in enumerate(self.level_node_centers()):
            self.draw_level_map_node(screen, index, center)

    def draw_level_map_node(self, screen, index, center):
        unlocked = self.is_level_unlocked(index)
        passed = index < self.latest_level_index
        selected = index == self.level_selected

        if selected and unlocked:
            glow = pygame.Surface((66, 66), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 240, 158, 66), (33, 33), 30)
            screen.blit(glow, (center[0] - 33, center[1] - 33))

        rim = (252, 252, 232) if selected and unlocked else (230, 238, 230)
        fill = (230, 72, 62) if passed else (247, 188, 63)
        if not unlocked:
            fill = (124, 137, 143)
            rim = (177, 188, 192)

        pygame.draw.circle(screen, (9, 28, 42), center, 18)
        pygame.draw.circle(screen, rim, center, 16)
        pygame.draw.circle(screen, fill, center, 13)

        label, _ = self.level_tabs[index]
        label_color = (238, 246, 235) if unlocked else (143, 159, 166)
        text = self.tab_font.render(label, True, label_color)
        shadow = self.tab_font.render(label, True, (8, 27, 39))
        label_y = center[1] + 38
        if index == 1:
            label_y = center[1] + 34
        screen.blit(shadow, shadow.get_rect(center=(center[0] + 2, label_y + 2)))
        screen.blit(text, text.get_rect(center=(center[0], label_y)))

    def draw_level_hover_panel(self, screen):
        if self.level_hovered is None:
            return

        rect = pygame.Rect(SCREEN_WIDTH - 378, 164, 334, 158)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(panel, panel.get_rect(), selected=True)

        mini_rect = pygame.Rect(18, 24, 118, 92)
        self.draw_level_minimap(panel, mini_rect, self.level_hovered)

        label, _ = self.level_tabs[self.level_hovered]
        title = self.tab_font.render(label, True, WHITE)
        panel.blit(title, (154, 28))

        locked = not self.is_level_unlocked(self.level_hovered)
        status = "Locked" if locked else "Unlocked"
        status_color = MUTED_TEXT if locked else (184, 236, 255)
        status_text = self.small_font.render(status, True, status_color)
        panel.blit(status_text, (154, 58))

        description = self.level_descriptions[self.level_hovered]
        self.draw_wrapped_text(panel, description, pygame.Rect(154, 84, 154, 56), MUTED_TEXT, self.small_font)
        screen.blit(panel, rect)

    def draw_level_minimap(self, surface, rect, level_index):
        self.draw_liquid_glass_surface(surface, rect, selected=False, radius=6)

        water_line = rect.bottom - 18
        pygame.draw.line(surface, (77, 151, 168), (rect.left + 8, water_line), (rect.right - 8, water_line), 2)
        start = (rect.left + 18, rect.bottom - 28)
        goal = (rect.right - 20, rect.top + 24)
        pygame.draw.circle(surface, (83, 188, 126), start, 7)
        pygame.draw.circle(surface, (223, 193, 92), goal, 7)

        if level_index == 0:
            pygame.draw.arc(surface, (184, 236, 255), (rect.left + 24, rect.top + 20, 62, 48), 0.15, 2.8, 3)
            pygame.draw.circle(surface, (139, 244, 166), (rect.left + 64, rect.top + 36), 4)
        elif level_index == 1:
            pygame.draw.line(surface, (184, 236, 255), (rect.left + 22, rect.top + 58), (rect.right - 28, rect.top + 42), 3)
            pygame.draw.circle(surface, (238, 248, 255), (rect.left + 64, rect.top + 64), 6, 2)
        else:
            pygame.draw.rect(surface, (28, 77, 86), (rect.left + 38, rect.top + 18, 12, 58), border_radius=3)
            pygame.draw.rect(surface, (28, 77, 86), (rect.left + 70, rect.top + 44, 36, 10), border_radius=3)
            for x in (rect.left + 58, rect.left + 78, rect.left + 98):
                pygame.draw.polygon(surface, (219, 228, 220), [(x, rect.top + 40), (x + 6, rect.top + 54), (x - 6, rect.top + 54)])

    def draw_wrapped_text(self, surface, text, rect, color, font):
        words = text.split()
        line = ""
        y = rect.top
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if font.size(candidate)[0] <= rect.width:
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

    def level_back_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 164, SCREEN_HEIGHT - 48, 144, 38)

    def load_back_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 164, SCREEN_HEIGHT - 48, 144, 38)

    def load_slot_rect(self, index):
        return pygame.Rect(230, 240 + index * 86, 500, 62)

    def load_slot_summary(self, slot_index):
        slot = self.save_manager.get_slot(slot_index) if self.save_manager else None
        if not slot:
            return f"Slot {slot_index + 1}", "Empty", 0
        return (
            slot.get("name") or f"Slot {slot_index + 1}",
            slot.get("latest_level_name", "Empty"),
            slot.get("seed_total", 0),
        )

    def draw_level_map_back_button(self, screen):
        rect = self.level_back_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(surface, surface.get_rect(), selected=False)
        label = self.tab_font.render("Back", True, WHITE)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        screen.blit(surface, rect)

    def draw_load_back_button(self, screen):
        rect = self.load_back_rect()
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (178, 210, 220, 62), surface.get_rect(), border_radius=8)
        pygame.draw.rect(surface, (230, 246, 250, 190), surface.get_rect(), 2, border_radius=8)
        pygame.draw.rect(surface, (52, 82, 98, 170), surface.get_rect().inflate(-10, -8), border_radius=6)
        label = self.tab_font.render("Back", True, WHITE)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        screen.blit(surface, rect)

    def draw_settings(self, screen):
        self.draw_back_button(screen)
        heading = self.subtitle_font.render("Settings", True, TEXT_COLOR)
        screen.blit(heading, heading.get_rect(center=(SCREEN_WIDTH / 2, 190)))

        panel = pygame.Rect(SCREEN_WIDTH / 2 - 190, 236, 380, 130)
        self.draw_glass_panel(screen, panel, selected=False)
        music = self.tab_font.render(f"Music  {self.music_volume}%", True, WHITE)
        sfx = self.tab_font.render(f"SFX  {self.sfx_volume}%", True, TEXT_COLOR)
        screen.blit(music, music.get_rect(center=(panel.centerx, panel.centery - 24)))
        screen.blit(sfx, sfx.get_rect(center=(panel.centerx, panel.centery + 28)))

        hint = self.small_font.render("Left / Right adjusts music volume", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_back_button(self, screen):
        rect = pygame.Rect(44, 38, 116, 42)
        self.draw_glass_panel(screen, rect, selected=False)
        label = self.small_font.render("Back", True, TEXT_COLOR)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_glass_tab(self, screen, rect, label, selected):
        self.draw_glass_panel(screen, rect, selected)
        if selected:
            pygame.draw.circle(screen, ENERGY_COLOR, (rect.left + 28, rect.centery), 5)
        text = self.tab_font.render(label, True, WHITE if selected else TEXT_COLOR)
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_glass_panel(self, screen, rect, selected):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(surface, surface.get_rect(), selected)
        screen.blit(surface, rect)

    def draw_liquid_glass_surface(self, surface, rect, selected, radius=8):
        shadow = rect.move(0, 5)
        pygame.draw.rect(surface, (0, 0, 0, 36), shadow, border_radius=radius)

        fill_alpha = 28 if selected else 17
        edge_alpha = 218 if selected else 142
        pygame.draw.rect(surface, (255, 255, 255, fill_alpha), rect, border_radius=radius)
        pygame.draw.rect(surface, (255, 255, 255, edge_alpha), rect, 2, border_radius=radius)
        pygame.draw.rect(surface, (255, 255, 255, 38), rect.inflate(-8, -8), 1, border_radius=max(4, radius - 2))

        highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(
            highlight,
            (255, 255, 255, 44 if selected else 28),
            (-rect.width * 0.2, -rect.height * 0.55, rect.width * 0.9, rect.height * 0.8),
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
            (rect.width // 2, rect.height // 3, rect.width // 2, rect.height // 2),
            math.radians(100),
            math.radians(235),
            2,
        )
        surface.blit(highlight, rect.topleft)

        if selected:
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 255, 255, 40), glow.get_rect().inflate(-10, -10), border_radius=max(4, radius - 2))
            pygame.draw.line(glow, (255, 255, 255, 82), (18, 10), (rect.width - 18, 10), 2)
            pygame.draw.line(glow, (*GOAL_COLOR, 70), (18, rect.height - 9), (rect.width - 18, rect.height - 9), 2)
            surface.blit(glow, rect.topleft)

    def current_tab_rects(self):
        if self.mode == "levels":
            return [self.level_tab_rect(index) for index in range(len(self.level_tabs))]
        if self.mode == "main":
            return [self.main_tab_rect(index) for index in range(len(self.main_tabs))]
        return []

    def main_tab_rect(self, index):
        width = 340
        height = 54
        gap = 12
        top = 166
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)

    def level_tab_rect(self, index):
        width = 300
        height = 54
        gap = 16
        top = 220
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)
