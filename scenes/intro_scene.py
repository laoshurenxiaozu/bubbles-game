from pathlib import Path

import pygame

from config import MUTED_TEXT, SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_COLOR, WHITE
from core.fonts import ui_font
from core.input import is_confirm, is_left, is_quit, is_right, key_value
from core.sounds import SoundManager


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
INTRO_IMAGE_PATHS = [
    ASSET_DIR / "intro_story_1.png",
    ASSET_DIR / "intro_story_2.png",
    ASSET_DIR / "intro_story_3.png",
    ASSET_DIR / "intro_story_4.png",
]


class IntroScene:
    def __init__(self, start_action, sfx_volume=80):
        self.start_action = start_action
        self.sound = SoundManager()
        self.sound.set_sfx_volume(sfx_volume)
        self.sound.play("transition")
        self.title_font = self.make_ui_font(24)
        self.body_font = self.make_ui_font(20)
        self.hint_font = self.make_ui_font(16)
        self.page_index = 0
        self.time = 0.0
        self.pages = self.build_pages()
        self.images = [self.load_image(path) for path in INTRO_IMAGE_PATHS]

    def make_ui_font(self, size):
        return ui_font(size)

    def build_pages(self):
        return [
            {
                "title": "很久以前，泡泡星生机盎然。",
                "body": [
                    "深海之下，生命之树守护着万物的循环。",
                    "它孕育生命种子，把生机送往陆地与海洋。",
                ],
            },
            {
                "title": "后来，魔息降临。",
                "body": [
                    "黑雾吞没陆地，清澈的海水被污染。",
                    "温和的生命化作失控的怪物，生命之树也开始枯萎。",
                ],
            },
            {
                "title": "而你，是最后幸存的泡泡。",
                "body": [
                    "在诸神最后的祝福中，你漂向生命之树仅存的根须。",
                    "那里沉睡着最后的生命种子，也藏着净化腐蚀的希望。",
                ],
            },
            {
                "title": "把希望带回生命之树。",
                "body": [
                    "收集生命种子，避开污染与怪物，穿过危险的深海。",
                    "每一颗种子都会唤醒一点生机。终有一日，春天会重回泡泡星。",
                ],
            },
        ]

    def load_image(self, path):
        if not path.exists():
            return None
        try:
            image = pygame.image.load(str(path))
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                action = self.handle_key(event)
                if action:
                    return action
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self.handle_click(event.pos)
                if action:
                    return action
        return None

    def handle_key(self, key):
        if key_value(key) == pygame.K_ESCAPE or is_quit(key):
            self.sound.play("menu_select")
            return self.start_action
        if is_right(key) or is_confirm(key):
            return self.advance_page()
        if is_left(key) or key_value(key) == pygame.K_BACKSPACE:
            previous = self.page_index
            self.page_index = max(0, self.page_index - 1)
            if previous != self.page_index:
                self.sound.play("menu_move")
        return None

    def handle_click(self, pos):
        if self.skip_button_rect().collidepoint(pos):
            self.sound.play("menu_select")
            return self.start_action
        if self.primary_button_rect().collidepoint(pos):
            return self.advance_page()
        if pos[0] < SCREEN_WIDTH * 0.4:
            previous = self.page_index
            self.page_index = max(0, self.page_index - 1)
            if previous != self.page_index:
                self.sound.play("menu_move")
            return None
        return self.advance_page()

    def advance_page(self):
        if self.page_index >= len(self.pages) - 1:
            self.sound.play("menu_select")
            return self.start_action
        self.page_index += 1
        self.sound.play("menu_move")
        return None

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        image = self.images[self.page_index]
        if image:
            screen.blit(image, (0, 0))
        else:
            screen.fill((9, 34, 48))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 12, 20, 86))
        screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(40, SCREEN_HEIGHT - 188, SCREEN_WIDTH - 80, 136)
        self.draw_text_panel(screen, panel_rect)

        page_text = self.hint_font.render(f"{self.page_index + 1} / {len(self.pages)}", True, WHITE)
        screen.blit(page_text, page_text.get_rect(topright=(SCREEN_WIDTH - 44, 28)))

        hint = "A/D 或方向键翻页"
        if self.page_index == len(self.pages) - 1:
            hint = "按回车或点击开始"
        hint_text = self.hint_font.render(hint, True, MUTED_TEXT)
        screen.blit(hint_text, hint_text.get_rect(center=(SCREEN_WIDTH / 2, 28)))

        self.draw_button(screen, self.skip_button_rect(), "跳过", selected=False)
        label = "下一页"
        if self.page_index == len(self.pages) - 1:
            label = "开始"
        self.draw_button(screen, self.primary_button_rect(), label, selected=True)

    def draw_text_panel(self, screen, rect):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (6, 18, 30, 190), panel.get_rect(), border_radius=18)
        pygame.draw.rect(panel, (228, 244, 250, 220), panel.get_rect(), 2, border_radius=18)
        pygame.draw.rect(panel, (255, 255, 255, 35), panel.get_rect().inflate(-18, -18), 1, border_radius=14)

        page = self.pages[self.page_index]
        title = self.title_font.render(page["title"], True, WHITE)
        panel.blit(title, (24, 20))

        y = 58
        for paragraph in page["body"]:
            y = self.draw_wrapped_text(panel, paragraph, pygame.Rect(24, y, rect.width - 48, 54), TEXT_COLOR)

        screen.blit(panel, rect)

    def draw_wrapped_text(self, surface, text, rect, color):
        words = self.wrap_units(text)
        line = ""
        y = rect.top
        for word in words:
            candidate = word if not line else f"{line}{word}"
            if self.body_font.size(candidate)[0] <= rect.width:
                line = candidate
                continue
            if line and word in "，。！？；：、）】》”’":
                line = candidate
                continue
            if line:
                surface.blit(self.body_font.render(line, True, color), (rect.left, y))
                y += self.body_font.get_linesize()
            line = word
        if line:
            surface.blit(self.body_font.render(line, True, color), (rect.left, y))
            y += self.body_font.get_linesize() + 6
        return y

    def wrap_units(self, text):
        if " " not in text:
            return list(text)
        units = []
        words = text.split(" ")
        for index, word in enumerate(words):
            if index:
                units.append(" ")
            units.append(word)
        return units

    def primary_button_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 188, SCREEN_HEIGHT - 48, 140, 36)

    def skip_button_rect(self):
        return pygame.Rect(48, SCREEN_HEIGHT - 48, 96, 36)

    def draw_button(self, screen, rect, label, selected):
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill = (95, 190, 128, 210) if selected else (28, 52, 70, 190)
        border = (247, 252, 240) if selected else (202, 226, 236)
        pygame.draw.rect(surface, fill, surface.get_rect(), border_radius=12)
        pygame.draw.rect(surface, border, surface.get_rect(), 2, border_radius=12)
        text = self.hint_font.render(label, True, WHITE)
        surface.blit(text, text.get_rect(center=surface.get_rect().center))
        screen.blit(surface, rect)
