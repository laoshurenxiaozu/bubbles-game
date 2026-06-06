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
from entities.objects import WildSeed
from entities.player import Player


BACKGROUND_PATH = Path(__file__).resolve().parents[1] / "assets" / "underwater_menu_bg.png"


class MenuScene:
    def __init__(self, save_manager=None, progress_data=None):
        self.save_manager = save_manager
        self.progress_data = progress_data or self.latest_save_progress_data() or self.default_progress_data()
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
            {"x": 86, "radius": 12, "duration": 4.8, "delay": 0.0, "drift": 12},
            {"x": 182, "radius": 20, "duration": 5.8, "delay": 1.2, "drift": 18},
            {"x": 342, "radius": 8, "duration": 4.2, "delay": 2.1, "drift": 10},
            {"x": 614, "radius": 16, "duration": 5.1, "delay": 0.7, "drift": 14},
            {"x": 806, "radius": 24, "duration": 6.4, "delay": 2.8, "drift": 20},
            {"x": 900, "radius": 10, "duration": 4.5, "delay": 1.7, "drift": 12},
            {"x": 468, "radius": 7, "duration": 3.9, "delay": 3.1, "drift": 8},
            {"x": 722, "radius": 13, "duration": 5.4, "delay": 3.8, "drift": 15},
        ]
        self.main_tabs = [
            ("Continue", "continue"),
            ("Start a New Game", "start_game"),
            ("Load Game", "load"),
            ("Settings", "settings"),
            ("Quit", "quit"),
        ]
        self.all_level_tabs = [
            ("Nursery Sea - 1", 0),
            ("Nursery Sea - 2", 1),
            ("Nursery Sea - 3", 2),
            ("Nursery Sea - 4", 3),
            ("Thorn Reef - 1", 4),
        ]
        self.all_level_descriptions = [
            "Learn the first bubble movement route and reach the safe leaf.",
            "Practice seed release and collect the free bubble in open water.",
            "Navigate walls and spikes while managing buoyancy with split bubbles.",
            "Route fresh bubbles from the vent while preserving enough seeds to finish strong.",
            "The first reef stage mixes narrow routes, side spikes, and split timing pressure.",
        ]
        self.unlock_seed_cost = 4
        self.unlock_animation_interval = 0.45
        self.unlock_confirmation = ""
        self.unlock_status_message = ""
        self.unlock_player = None
        self.unlock_emitted = []
        self.unlock_emit_count = 0
        self.unlock_timer = 0.0
        self.unlock_failed = False
        self.refresh_progress_state()

    def make_font(self, size):
        return pygame.font.Font(None, int(size))

    def load_background_image(self):
        if not BACKGROUND_PATH.exists():
            return None
        try:
            image = pygame.image.load(str(BACKGROUND_PATH))
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def level_star_count(self, level_index):
        stars = self.progress_data.get("stars_by_level", {})
        if level_index in stars:
            return stars[level_index]
        return stars.get(str(level_index))

    def draw_small_star(self, surface, center, outer_radius, color, filled=True):
        inner_radius = outer_radius * 0.46
        points = []
        for index in range(10):
            angle = -math.pi / 2 + index * (math.pi / 5)
            radius = outer_radius if index % 2 == 0 else inner_radius
            points.append(
                (
                    center[0] + math.cos(angle) * radius,
                    center[1] + math.sin(angle) * radius,
                )
            )
        if filled:
            pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, color, points, 2)

    def refresh_progress_state(self):
        self.main_tabs = self.build_main_tabs()
        self.current_region = self.progress_data.get("current_region", "nursery")
        self.viewed_region = self.progress_data.get("viewed_region", self.current_region)
        self.thorn_reef_unlocked = self.progress_data.get("thorn_reef_unlocked", False)
        self.latest_level_index = min(
            self.progress_data.get("unlocked_levels", 0),
            len(self.all_level_tabs) - 1,
        )
        self.visible_level_indices = self.region_level_indices()
        current_level_index = self.progress_data.get("current_level_index", self.visible_level_indices[0])
        if current_level_index not in self.visible_level_indices:
            current_level_index = self.visible_level_indices[0]
        self.level_selected = current_level_index
        self.selected = min(self.selected, len(self.main_tabs) - 1)

    def build_main_tabs(self):
        tabs = []
        if self.progress_data.get("slot_index") is not None:
            tabs.append(("Continue", "continue"))
        tabs.append(("Start a New Game", "start_game"))
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
                if not self.try_switch_region_page(-1):
                    self.move_level_selection(-1)
            elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                if not self.try_switch_region_page(1):
                    self.move_level_selection(1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_map_selection()
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
        elif self.mode == "unlock_confirm":
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.mode = "levels"
                self.unlock_confirmation = ""
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_y):
                self.start_region_unlock()
            elif key in (pygame.K_n,):
                self.mode = "levels"
                self.unlock_confirmation = ""
        elif self.mode == "unlock_result":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                if self.unlock_failed:
                    self.reset_to_nursery_start()
                self.mode = "levels"
                self.unlock_status_message = ""
        return None

    def activate_main_tab(self, index):
        action = self.main_tabs[index][1]
        if action == "start_game":
            fresh_progress = self.default_progress_data()
            return {
                "type": "start",
                "level": fresh_progress.get("current_level_index", 0),
                "slot_index": None,
                "save_data": fresh_progress,
            }
        if action == "continue":
            if self.progress_data.get("slot_index") is None:
                self.load_message = "No saved progress to continue"
                return None
            return {
                "type": "start",
                "level": self.progress_data.get("current_level_index", 0),
                "slot_index": self.progress_data.get("slot_index"),
                "save_data": self.progress_data,
            }
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
            if level_index == "gate":
                self.level_selected = "gate"
                return
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
            hit = self.level_node_at_pos(pos)
            if hit == "gate":
                return self.begin_region_unlock()
            return self.activate_level_node(hit)
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

        if self.mode in ("levels", "settings", "unlock_confirm", "unlock_result"):
            back_rect = pygame.Rect(44, 38, 116, 42)
            if back_rect.collidepoint(pos):
                self.mode = "main"
        return None

    def default_progress_data(self):
        return {
            "current_level_index": 0,
            "latest_level_index": 0,
            "unlocked_levels": 0,
            "player_bubbles": 1,
            "player_seeds": 0,
            "seed_total": 0,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
        }

    def latest_save_progress_data(self):
        if not self.save_manager:
            return None
        slot_index, slot = self.save_manager.latest_slot()
        if not slot:
            return None
        slot["slot_index"] = slot_index
        return slot

    def region_level_indices(self):
        if self.viewed_region == "thorn_reef":
            return [4]
        return [0, 1, 2, 3]

    @property
    def level_tabs(self):
        return self.visible_level_tabs()

    def visible_level_tabs(self):
        return [self.all_level_tabs[index] for index in self.visible_level_indices]

    def visible_level_descriptions(self):
        return [self.all_level_descriptions[index] for index in self.visible_level_indices]

    def show_region_gate(self):
        return self.viewed_region == "nursery" and not self.thorn_reef_unlocked and self.latest_level_index >= 3

    def selectable_map_items(self):
        items = list(self.visible_level_indices)
        if self.show_region_gate():
            items.append("gate")
        return items

    def move_level_selection(self, delta):
        items = self.selectable_map_items()
        current = self.level_selected if self.level_selected in items else items[0]
        index = items.index(current)
        self.level_selected = items[(index + delta) % len(items)]

    def try_switch_region_page(self, direction):
        if direction < 0:
            if self.viewed_region == "thorn_reef" and self.level_selected == 4:
                self.viewed_region = "nursery"
                self.visible_level_indices = self.region_level_indices()
                self.level_selected = self.visible_level_indices[-1]
                self.level_hovered = None
                self.map_message = "Nursery Sea"
                return True
            return False

        if self.viewed_region == "nursery":
            if self.thorn_reef_unlocked and self.level_selected == self.visible_level_indices[-1]:
                self.viewed_region = "thorn_reef"
                self.visible_level_indices = self.region_level_indices()
                self.level_selected = 4
                self.level_hovered = None
                self.map_message = "Thorn Reef"
                return True
            if self.show_region_gate() and self.level_selected == self.visible_level_indices[-1]:
                self.level_selected = "gate"
                self.map_message = f"Spend {self.unlock_seed_cost} seeds to unlock Thorn Reef"
                return True
        return False

    def activate_map_selection(self):
        if self.level_selected == "gate":
            return self.begin_region_unlock()
        return self.activate_level_node(self.level_selected)

    def activate_level_node(self, level_index):
        if level_index is None or not self.is_level_playable(level_index):
            if level_index is not None and level_index in self.visible_level_indices:
                self.map_message = "Nursery Sea can no longer be entered from Thorn Reef"
            return None
        self.level_selected = level_index
        return {
            "type": "start",
            "level": self.all_level_tabs[level_index][1],
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
        return level_index in self.visible_level_indices and level_index <= self.latest_level_index

    def is_level_playable(self, level_index):
        if not self.is_level_unlocked(level_index):
            return False
        if self.current_region == "thorn_reef" and level_index < 4:
            return False
        return True

    def level_node_centers(self):
        count = len(self.visible_level_indices)
        if count <= 1:
            return [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]

        if self.viewed_region == "thorn_reef":
            route = [(520, 306)]
        else:
            route = [
                (128, 388),
                (342, 302),
                (586, 370),
                (768, 288),
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
                return self.visible_level_indices[index]
        if self.show_region_gate() and math.dist(pos, self.region_gate_center()) <= 28:
            return "gate"
        return None

    def update(self, dt):
        self.time += dt
        if self.mode == "unlock_anim":
            self.update_region_unlock(dt)

    def draw(self, screen):
        if self.mode == "levels":
            self.draw_levels(screen)
            return
        if self.mode == "load":
            self.draw_load(screen)
            return
        if self.mode in ("unlock_confirm", "unlock_anim", "unlock_result"):
            self.draw_levels(screen)
            self.draw_unlock_overlay(screen)
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

        for bubble in self.bubbles:
            self.draw_rising_bubble(screen, bubble)

    def bubble_position_at_time(self, bubble, elapsed):
        progress = ((elapsed + bubble["delay"]) % bubble["duration"]) / bubble["duration"]
        x = bubble["x"] + math.sin(progress * math.tau * 1.4 + bubble["x"]) * bubble["drift"]
        y = SCREEN_HEIGHT + 42 - progress * (SCREEN_HEIGHT + 110)
        return (int(x), int(y))

    def draw_rising_bubble(self, screen, bubble):
        center = self.bubble_position_at_time(bubble, self.time)
        progress = ((self.time + bubble["delay"]) % bubble["duration"]) / bubble["duration"]
        radius = bubble["radius"]
        alpha = int(210 * min(1.0, progress * 5.0, (1.0 - progress) * 5.0))
        if alpha <= 0:
            return

        bubble_surface = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        local_center = (radius * 3 // 2, radius * 3 // 2)
        pygame.draw.circle(bubble_surface, (180, 235, 255, alpha), local_center, radius, 2)
        pygame.draw.circle(
            bubble_surface,
            (244, 253, 255, min(255, alpha + 30)),
            (local_center[0] - radius // 3, local_center[1] - radius // 3),
            max(2, radius // 5),
        )
        screen.blit(bubble_surface, (center[0] - local_center[0], center[1] - local_center[1]))

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
        self.draw_region_gate(screen)
        self.draw_level_hover_panel(screen)
        self.draw_level_map_back_button(screen)

        title = self.title_font.render("Level Map", True, (242, 252, 226))
        shadow = self.title_font.render("Level Map", True, (11, 35, 55))
        screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH / 2 + 3, 59)))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, 55)))

        subtitle_text = self.map_message or ("Thorn Reef" if self.viewed_region == "thorn_reef" else "Nursery Sea")
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
        if self.show_region_gate() and centers:
            gate_color = (247, 188, 63) if self.latest_level_index >= 3 else (105, 116, 122)
            self.draw_dotted_line(screen, centers[-1], self.region_gate_center(), gate_color)

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
        for display_index, center in enumerate(self.level_node_centers()):
            self.draw_level_map_node(screen, self.visible_level_indices[display_index], center)

    def region_gate_center(self):
        return (906, 190)

    def draw_region_gate(self, screen):
        if not self.show_region_gate():
            return
        center = self.region_gate_center()
        selected = self.level_selected == "gate"
        unlocked = self.can_attempt_region_unlock()
        rim = (252, 252, 232) if selected else (230, 238, 230)
        fill = (247, 188, 63) if unlocked else (124, 137, 143)
        pygame.draw.circle(screen, (9, 28, 42), center, 22)
        pygame.draw.circle(screen, rim, center, 20)
        pygame.draw.circle(screen, fill, center, 17)
        lock_text = self.small_font.render("4", True, (9, 28, 42))
        screen.blit(lock_text, lock_text.get_rect(center=center))
        label = self.small_font.render("Unlock Thorn Reef", True, WHITE if unlocked else MUTED_TEXT)
        screen.blit(label, label.get_rect(center=(center[0], center[1] + 42)))

    def draw_level_map_node(self, screen, index, center):
        unlocked = self.is_level_unlocked(index)
        playable = self.is_level_playable(index)
        passed = index < self.latest_level_index
        selected = index == self.level_selected

        if selected and playable:
            glow = pygame.Surface((66, 66), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 240, 158, 66), (33, 33), 30)
            screen.blit(glow, (center[0] - 33, center[1] - 33))

        rim = (252, 252, 232) if selected and playable else (230, 238, 230)
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

        label, _ = self.all_level_tabs[index]
        if not unlocked:
            label_color = (143, 159, 166)
        elif not playable:
            label_color = (164, 176, 182)
        else:
            label_color = (238, 246, 235)
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

        rect = self.level_hover_panel_rect()
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_liquid_glass_surface(panel, panel.get_rect(), selected=True)

        if self.level_hovered == "gate":
            title = self.tab_font.render("Thorn Reef Gate", True, WHITE)
            panel.blit(title, (24, 28))
            status = f"Spend {self.unlock_seed_cost} seeds to unlock"
            status_text = self.small_font.render(status, True, (184, 236, 255))
            panel.blit(status_text, (24, 58))
            description = "Your bubble body must survive four 1:1 seed releases to cross into the next sea."
            self.draw_wrapped_text(panel, description, pygame.Rect(24, 84, 270, 56), MUTED_TEXT, self.small_font)
        else:
            mini_rect = pygame.Rect(18, 24, 118, 92)
            self.draw_level_minimap(panel, mini_rect, self.level_hovered)

            label, _ = self.all_level_tabs[self.level_hovered]
            title = self.tab_font.render(label, True, WHITE)
            panel.blit(title, (154, 28))

            locked = not self.is_level_unlocked(self.level_hovered)
            playable = self.is_level_playable(self.level_hovered)
            if locked:
                status = "Locked"
                status_color = MUTED_TEXT
            elif not playable:
                status = "Past Region"
                status_color = (190, 200, 205)
            else:
                status = "Unlocked"
                status_color = (184, 236, 255)
            status_text = self.small_font.render(status, True, status_color)
            panel.blit(status_text, (154, 58))

            stars = self.level_star_count(self.level_hovered)
            if stars is not None:
                for index in range(3):
                    filled = index < int(stars)
                    color = (255, 221, 126) if filled else (120, 115, 96)
                    self.draw_small_star(panel, (174 + index * 28, 84), 9, color, filled=filled)
                description_top = 102
            else:
                description_top = 84

            description = self.all_level_descriptions[self.level_hovered]
            self.draw_wrapped_text(panel, description, pygame.Rect(154, description_top, 154, 56), MUTED_TEXT, self.small_font)
        screen.blit(panel, rect)

    def level_hover_panel_rect(self):
        panel_width = 334
        panel_height = 158
        margin = 24
        gap = 38

        center = self.level_hover_center()
        if center is None:
            return pygame.Rect(SCREEN_WIDTH - panel_width - margin, 164, panel_width, panel_height)

        x = center[0] + gap
        if x + panel_width + margin > SCREEN_WIDTH:
            x = center[0] - gap - panel_width
        x = max(margin, min(x, SCREEN_WIDTH - panel_width - margin))

        y = center[1] - panel_height // 2
        y = max(134, min(y, SCREEN_HEIGHT - panel_height - 64))
        return pygame.Rect(x, y, panel_width, panel_height)

    def level_hover_center(self):
        if self.level_hovered == "gate":
            return self.region_gate_center()
        if self.level_hovered in self.visible_level_indices:
            display_index = self.visible_level_indices.index(self.level_hovered)
            return self.level_node_centers()[display_index]
        return None

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
            return [self.level_tab_rect(index) for index in range(len(self.visible_level_indices))]
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

    def can_attempt_region_unlock(self):
        return self.progress_data.get("player_seeds", 0) >= self.unlock_seed_cost

    def begin_region_unlock(self):
        self.unlock_confirmation = (
            f"Spend {self.unlock_seed_cost} seeds to unlock Thorn Reef?"
            if self.can_attempt_region_unlock()
            else f"You need {self.unlock_seed_cost} seeds to unlock Thorn Reef"
        )
        self.mode = "unlock_confirm"
        return None

    def start_region_unlock(self):
        if not self.can_attempt_region_unlock():
            self.unlock_status_message = f"You need {self.unlock_seed_cost} seeds first"
            self.mode = "unlock_result"
            self.unlock_failed = False
            return
        player_pos = (120, 150)
        self.unlock_player = Player(player_pos)
        self.unlock_player.bubble_count = self.progress_data.get("player_bubbles", 1)
        self.unlock_player.seed_count = self.progress_data.get("player_seeds", 0)
        self.unlock_emitted = []
        self.unlock_emit_count = 0
        self.unlock_timer = self.unlock_animation_interval
        self.unlock_failed = False
        self.mode = "unlock_anim"

    def update_region_unlock(self, dt):
        self.unlock_timer -= dt
        if self.unlock_timer > 0:
            return
        self.unlock_timer += self.unlock_animation_interval
        if self.unlock_emit_count >= self.unlock_seed_cost:
            self.finish_region_unlock()
            return
        if self.unlock_player.bubble_count <= 1 or self.unlock_player.seed_count <= 0:
            self.unlock_player.bubble_count = 0
            self.unlock_failed = True
            self.unlock_status_message = "Bubble burst. Return to Nursery Sea - 1."
            self.mode = "unlock_result"
            return
        self.unlock_player.bubble_count -= 1
        self.unlock_player.seed_count -= 1
        emitted = WildSeed(
            250 + self.unlock_emit_count * 62,
            152,
        )
        self.unlock_emitted.append(emitted)
        self.unlock_emit_count += 1
        if self.unlock_emit_count >= self.unlock_seed_cost:
            self.finish_region_unlock()

    def finish_region_unlock(self):
        self.progress_data["player_bubbles"] = self.unlock_player.bubble_count
        self.progress_data["player_seeds"] = self.unlock_player.seed_count
        self.progress_data["seed_total"] = self.unlock_player.seed_count
        self.progress_data["thorn_reef_unlocked"] = True
        self.progress_data["current_region"] = "thorn_reef"
        self.progress_data["viewed_region"] = "thorn_reef"
        self.progress_data["current_level_index"] = 4
        self.progress_data["latest_level_index"] = max(self.progress_data.get("latest_level_index", 0), 4)
        self.progress_data["unlocked_levels"] = max(self.progress_data.get("unlocked_levels", 0), 4)
        self.thorn_reef_unlocked = True
        self.current_region = "thorn_reef"
        self.refresh_progress_state()
        self.level_selected = 4
        self.map_message = "Thorn Reef unlocked"
        self.mode = "levels"

    def reset_to_nursery_start(self):
        slot_index = self.progress_data.get("slot_index")
        self.progress_data = self.default_progress_data()
        if slot_index is not None:
            self.progress_data["slot_index"] = slot_index
        self.refresh_progress_state()
        self.level_selected = 0
        self.map_message = "The bubble burst. Start Nursery Sea again."

    def draw_unlock_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 14, 24, 180))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(170, 132, 620, 280)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (14, 55, 76, 238), surface.get_rect(), border_radius=26)
        pygame.draw.rect(surface, (189, 231, 240), surface.get_rect(), 3, border_radius=26)
        title = self.tab_font.render("Unlock Thorn Reef", True, WHITE)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 40)))
        if self.mode == "unlock_confirm":
            body = self.subtitle_font.render(self.unlock_confirmation, True, TEXT_COLOR)
            surface.blit(body, body.get_rect(center=(panel.width / 2, 112)))
            hint = self.small_font.render("Enter to confirm, Esc to cancel", True, MUTED_TEXT)
            surface.blit(hint, hint.get_rect(center=(panel.width / 2, 240)))
        else:
            if self.unlock_player:
                self.unlock_player.draw(surface)
            for seed in self.unlock_emitted:
                clone = WildSeed(seed.x, seed.y)
                clone.draw(surface)
            if self.mode == "unlock_anim":
                hint = self.small_font.render("Offering 4 seed-bubbles to cross the reef...", True, TEXT_COLOR)
            else:
                hint = self.small_font.render(self.unlock_status_message, True, (255, 221, 126))
            surface.blit(hint, hint.get_rect(center=(panel.width / 2, 238)))
        screen.blit(surface, panel.topleft)
