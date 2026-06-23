from copy import deepcopy

import pygame

from core.save_manager import SaveManager
from core.sounds import SoundManager
from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from scenes.ending_scene import EndingScene
from scenes.intro_scene import IntroScene
from scenes.level_scene import LevelScene
from scenes.menu_scene import MenuScene


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.sound = SoundManager()
        self.sound.init()
        self.save_manager = SaveManager()
        self.session_progress = None
        self.session_dirty = False
        self.scene = MenuScene(
            save_manager=self.save_manager,
            session_progress=self.session_progress,
            session_dirty=self.session_dirty,
            sfx_volume=self.sound.get_sfx_volume(),
            music_volume=self.sound.get_music_volume(),
        )
        self.running = True

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    action = getattr(self.scene, "request_window_close_action", lambda: {"type": "quit"})()
                    self.handle_action(action)

            action = self.scene.handle_events(events)
            self.handle_action(action)
            self.scene.update(dt)
            self.sync_session_progress_from_scene()
            self.sync_scene_volume()
            pending_action = getattr(self.scene, "consume_pending_action", lambda: None)()
            self.handle_action(pending_action)
            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

    def handle_action(self, action):
        if not action:
            return
        sfx_vol = self.sound.get_sfx_volume()
        music_vol = self.sound.get_music_volume()
        if action["type"] == "start":
            self.update_session_progress(action.get("save_data"))
            self.scene = LevelScene(
                level_index=action.get("level", 0),
                save_manager=self.save_manager,
                slot_index=action.get("slot_index"),
                save_data=action.get("save_data"),
                sfx_volume=sfx_vol,
                music_volume=music_vol,
            )
            self.sound.play_music("level")
        elif action["type"] == "intro":
            self.sound.stop_music()
            self.scene = IntroScene(start_action=action["start_action"], sfx_volume=sfx_vol)
        elif action["type"] == "ending":
            self.update_session_progress(action.get("progress_data"))
            self.sound.stop_music()
            self.scene = EndingScene(progress_data=action.get("progress_data"), sfx_volume=sfx_vol)
        elif action["type"] == "menu":
            self.update_session_progress(action.get("progress_data"))
            self.sound.stop_music()
            self.scene = MenuScene(
                save_manager=self.save_manager,
                progress_data=action.get("progress_data"),
                session_progress=self.session_progress,
                session_dirty=self.session_dirty,
                sfx_volume=sfx_vol,
                music_volume=music_vol,
            )
        elif action["type"] == "quit":
            self.sound.stop_music()
            self.running = False

    def sync_scene_volume(self):
        """Sync scene volume settings back to the SoundManager."""
        scene_sfx_vol = getattr(self.scene, "sfx_volume", None)
        if scene_sfx_vol is not None and scene_sfx_vol != self.sound.get_sfx_volume():
            self.sound.set_sfx_volume(scene_sfx_vol)
        scene_music_vol = getattr(self.scene, "music_volume", None)
        if scene_music_vol is not None and scene_music_vol != self.sound.get_music_volume():
            self.sound.set_music_volume(scene_music_vol)

    def sync_session_progress_from_scene(self):
        provider = getattr(self.scene, "session_progress_state", None)
        if not callable(provider):
            return
        self.update_session_progress(provider())

    def update_session_progress(self, progress_data):
        if progress_data and progress_data.get("has_started_game"):
            self.session_progress = deepcopy(progress_data)
            self.session_dirty = self.compute_session_dirty(self.session_progress)
        else:
            self.session_progress = None
            self.session_dirty = False
        if hasattr(self.scene, "session_progress"):
            self.scene.session_progress = deepcopy(self.session_progress) if self.session_progress else None
        if hasattr(self.scene, "session_dirty"):
            self.scene.session_dirty = self.session_dirty

    def compute_session_dirty(self, progress_data):
        if not progress_data:
            return False
        slot_index = progress_data.get("slot_index")
        if slot_index is None:
            return True
        saved = self.save_manager.get_slot(slot_index)
        if not saved:
            return True
        saved_progress = dict(saved)
        saved_progress["slot_index"] = slot_index
        return self.normalize_progress(progress_data) != self.normalize_progress(saved_progress)

    def normalize_progress(self, progress_data):
        return {
            "slot_index": progress_data.get("slot_index"),
            "current_level_index": progress_data.get("current_level_index", 0),
            "latest_level_index": progress_data.get("latest_level_index", 0),
            "unlocked_levels": progress_data.get("unlocked_levels", 0),
            "player_bubbles": progress_data.get("player_bubbles", 1),
            "player_seeds": progress_data.get("player_seeds", 0),
            "seed_total": progress_data.get("seed_total", 0),
            "completed_level_states": progress_data.get("completed_level_states", {}),
            "stars_by_level": progress_data.get("stars_by_level", {}),
            "current_region": progress_data.get("current_region", "nursery"),
            "thorn_reef_unlocked": progress_data.get("thorn_reef_unlocked", False),
            "restart_hint_enabled": progress_data.get("restart_hint_enabled", True),
        }
