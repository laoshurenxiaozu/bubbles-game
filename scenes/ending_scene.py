from pathlib import Path

import pygame

from config import MUTED_TEXT, SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_COLOR, WHITE
from core.input import is_confirm


ENDING_BACKGROUND_PATH = Path(__file__).resolve().parents[1] / "assets" / "intro_story_1.png"


class EndingScene:
    def __init__(self, progress_data=None):
        self.progress_data = progress_data or {}
        self.title_font = self.make_font(42)
        self.body_font = self.make_font(24)
        self.hint_font = self.make_font(18)
        self.background_image = self.load_background_image()

    def make_font(self, size):
        return pygame.font.Font(None, int(size))

    def load_background_image(self):
        if not ENDING_BACKGROUND_PATH.exists():
            return None
        try:
            image = pygame.image.load(str(ENDING_BACKGROUND_PATH))
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and (is_confirm(event) or event.key == pygame.K_ESCAPE):
                return {"type": "menu", "progress_data": self.progress_data}
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return {"type": "menu", "progress_data": self.progress_data}
        return None

    def update(self, dt):
        return None

    def draw(self, screen):
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill((10, 44, 61))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((2, 12, 20, 112))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(120, 98, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 196)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(surface, (7, 28, 40, 208), surface.get_rect(), border_radius=24)
        pygame.draw.rect(surface, (222, 243, 248), surface.get_rect(), 2, border_radius=24)

        title = self.title_font.render("Bubble Star Lives Again", True, WHITE)
        surface.blit(title, title.get_rect(center=(panel.width / 2, 54)))

        paragraphs = [
            "The final life seed returns to the Tree of Life.",
            "Light spreads through the roots, the corruption breaks apart, and the deep sea begins to breathe again.",
            "Because of your journey, spring has found Bubble Star once more.",
        ]
        y = 112
        for paragraph in paragraphs:
            y = self.draw_wrapped_text(
                surface,
                paragraph,
                pygame.Rect(44, y, panel.width - 88, 76),
                TEXT_COLOR,
            )

        hint = self.hint_font.render("Press Enter or click to return to the main menu", True, MUTED_TEXT)
        surface.blit(hint, hint.get_rect(center=(panel.width / 2, panel.height - 34)))
        screen.blit(surface, panel.topleft)

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
                rendered = self.body_font.render(line, True, color)
                surface.blit(rendered, (rect.left, y))
                y += self.body_font.get_linesize()
            line = word
        if line:
            rendered = self.body_font.render(line, True, color)
            surface.blit(rendered, (rect.left, y))
            y += self.body_font.get_linesize() + 14
        return y

    def session_progress_state(self):
        if self.progress_data and self.progress_data.get("has_started_game"):
            return self.progress_data
        return None
