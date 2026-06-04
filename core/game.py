import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from scenes.level_scene import LevelScene
from scenes.menu_scene import MenuScene


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.scene = MenuScene()
        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            action = self.scene.handle_events(events)
            self.handle_action(action)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

    def handle_action(self, action):
        if not action:
            return
        if action["type"] == "start":
            self.scene = LevelScene(level_index=action.get("level", 0))
        elif action["type"] == "menu":
            self.scene = MenuScene()
        elif action["type"] == "quit":
            self.running = False
