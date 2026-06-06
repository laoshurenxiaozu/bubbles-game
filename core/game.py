import pygame

from core.save_manager import SaveManager
from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from scenes.intro_scene import IntroScene
from scenes.level_scene import LevelScene
from scenes.menu_scene import MenuScene


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.save_manager = SaveManager()
        self.scene = MenuScene(save_manager=self.save_manager)
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
            self.scene = LevelScene(
                level_index=action.get("level", 0),
                save_manager=self.save_manager,
                slot_index=action.get("slot_index"),
                save_data=action.get("save_data"),
            )
        elif action["type"] == "intro":
            self.scene = IntroScene(start_action=action["start_action"])
        elif action["type"] == "menu":
            self.scene = MenuScene(
                save_manager=self.save_manager,
                progress_data=action.get("progress_data"),
            )
        elif action["type"] == "quit":
            self.running = False
