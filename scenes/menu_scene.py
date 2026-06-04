import math

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


class MenuScene:
    def __init__(self):
        self.title_font = self.make_font(82)
        self.subtitle_font = self.make_font(24)
        self.tab_font = self.make_font(30)
        self.small_font = self.make_font(18)
        self.mode = "main"
        self.selected = 0
        self.level_selected = 0
        self.time = 0.0
        self.music_volume = 80
        self.sfx_volume = 80
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
            ("Level Catalog", "levels"),
            ("Settings", "settings"),
            ("Quit", "quit"),
        ]
        self.level_tabs = [
            ("Tutorial 1", 0),
            ("Tutorial 2", 1),
            ("Tutorial 3", 2),
        ]

    def make_font(self, size):
        return pygame.font.Font(None, int(size))

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
            elif key in (pygame.K_UP, pygame.K_w):
                self.level_selected = (self.level_selected - 1) % len(self.level_tabs)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.level_selected = (self.level_selected + 1) % len(self.level_tabs)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                return {"type": "start", "level": self.level_tabs[self.level_selected][1]}
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
            return {"type": "start", "level": 0}
        if action == "continue":
            return {"type": "start", "level": 0}
        if action == "levels":
            self.mode = "levels"
        elif action == "settings":
            self.mode = "settings"
        elif action == "quit":
            return {"type": "quit"}
        return None

    def update_hover(self, pos):
        tabs = self.current_tab_rects()
        for index, rect in enumerate(tabs):
            if rect.collidepoint(pos):
                if self.mode == "levels":
                    self.level_selected = index
                elif self.mode == "main":
                    self.selected = index
                return

    def handle_click(self, pos):
        tabs = self.current_tab_rects()
        for index, rect in enumerate(tabs):
            if rect.collidepoint(pos):
                if self.mode == "levels":
                    return {"type": "start", "level": self.level_tabs[index][1]}
                if self.mode == "main":
                    self.selected = index
                    return self.activate_main_tab(index)

        if self.mode in ("levels", "settings"):
            back_rect = pygame.Rect(44, 38, 116, 42)
            if back_rect.collidepoint(pos):
                self.mode = "main"
        return None

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        self.draw_background(screen)
        self.draw_title(screen)
        if self.mode == "main":
            self.draw_main(screen)
        elif self.mode == "levels":
            self.draw_levels(screen)
        else:
            self.draw_settings(screen)

    def draw_background(self, screen):
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

        hint = self.small_font.render("Use arrows or W/S, Enter to choose", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

    def draw_levels(self, screen):
        self.draw_back_button(screen)
        heading = self.subtitle_font.render("Level Catalog", True, TEXT_COLOR)
        screen.blit(heading, heading.get_rect(center=(SCREEN_WIDTH / 2, 172)))

        for index, (label, _) in enumerate(self.level_tabs):
            rect = self.level_tab_rect(index)
            self.draw_glass_tab(screen, rect, label, index == self.level_selected)

        hint = self.small_font.render("Unlocked training levels", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 34)))

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
        fill = (235, 250, 255, 48 if selected else 30)
        edge = (226, 250, 255, 210 if selected else 130)
        shine = (255, 255, 255, 54 if selected else 30)
        pygame.draw.rect(surface, fill, surface.get_rect(), border_radius=8)
        pygame.draw.rect(surface, edge, surface.get_rect(), 2, border_radius=8)
        pygame.draw.line(surface, shine, (18, 10), (rect.width - 18, 10), 2)
        if selected:
            pygame.draw.rect(surface, (*GOAL_COLOR, 35), surface.get_rect().inflate(-8, -8), border_radius=6)
        screen.blit(surface, rect)

    def current_tab_rects(self):
        if self.mode == "levels":
            return [self.level_tab_rect(index) for index in range(len(self.level_tabs))]
        if self.mode == "main":
            return [self.main_tab_rect(index) for index in range(len(self.main_tabs))]
        return []

    def main_tab_rect(self, index):
        width = 340
        height = 54
        gap = 14
        top = 190
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)

    def level_tab_rect(self, index):
        width = 300
        height = 54
        gap = 16
        top = 220
        return pygame.Rect((SCREEN_WIDTH - width) // 2, top + index * (height + gap), width, height)
