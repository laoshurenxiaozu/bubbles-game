from pathlib import Path

import pygame

from config import MUTED_TEXT, SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_COLOR, WHITE


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
INTRO_IMAGE_PATHS = [
    ASSET_DIR / "intro_story_1.png",
    ASSET_DIR / "intro_story_2.png",
    ASSET_DIR / "intro_story_3.png",
    ASSET_DIR / "intro_story_4.png",
]


class IntroScene:
    def __init__(self, start_action):
        self.start_action = start_action
        self.title_font = self.make_font(26)
        self.body_font = self.make_font(22)
        self.hint_font = self.make_font(18)
        self.page_index = 0
        self.time = 0.0
        self.pages = self.build_pages()
        self.images = [self.load_image(path) for path in INTRO_IMAGE_PATHS]

    def make_font(self, size):
        return pygame.font.Font(None, int(size))

    def build_pages(self):
        return [
            {
                "title": "Long ago, Bubble Star was full of life.",
                "body": [
                    "Deep beneath the sea stood the Tree of Life, sustaining the cycle of every living thing in the world.",
                    "It nurtured life seeds without end, scattering vitality across the land and ocean so all creatures could thrive.",
                ],
            },
            {
                "title": "Then the demonic corruption arrived.",
                "body": [
                    "Black miasma swallowed the land, the clear sea was poisoned, and gentle creatures became mindless polluted monsters.",
                    "The Tree of Life was consumed by evil, its branches withered, and Bubble Star began to fade toward ruin.",
                ],
            },
            {
                "title": "And you are the last surviving bubble.",
                "body": [
                    "Guided by the final blessing of the gods, you drift to the last living roots of the Tree.",
                    "There lie the final life seeds, carrying the purest life force and the only hope of cleansing the corruption.",
                ],
            },
            {
                "title": "You must carry hope back to the Tree.",
                "body": [
                    "Collect the life seeds, evade pollution and monsters, and cross the perilous deep sea to return them to the Tree of Life.",
                    "Each seed restores a little more life. And when the final seed returns, spring will come to Bubble Star once again.",
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
                action = self.handle_key(event.key)
                if action:
                    return action
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                action = self.handle_click(event.pos)
                if action:
                    return action
        return None

    def handle_key(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_q):
            return self.start_action
        if key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE, pygame.K_RETURN):
            return self.advance_page()
        if key in (pygame.K_LEFT, pygame.K_a, pygame.K_BACKSPACE):
            self.page_index = max(0, self.page_index - 1)
        return None

    def handle_click(self, pos):
        if self.skip_button_rect().collidepoint(pos):
            return self.start_action
        if self.primary_button_rect().collidepoint(pos):
            return self.advance_page()
        if pos[0] < SCREEN_WIDTH * 0.4:
            self.page_index = max(0, self.page_index - 1)
            return None
        return self.advance_page()

    def advance_page(self):
        if self.page_index >= len(self.pages) - 1:
            return self.start_action
        self.page_index += 1
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

        hint = "A/D or Left/Right to turn pages"
        if self.page_index == len(self.pages) - 1:
            hint = "Press Enter or click Start to begin"
        hint_text = self.hint_font.render(hint, True, MUTED_TEXT)
        screen.blit(hint_text, hint_text.get_rect(center=(SCREEN_WIDTH / 2, 28)))

        self.draw_button(screen, self.skip_button_rect(), "Skip", selected=False)
        label = "Next"
        if self.page_index == len(self.pages) - 1:
            label = "Start"
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
        words = text.split()
        line = ""
        y = rect.top
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if self.body_font.size(candidate)[0] <= rect.width:
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
