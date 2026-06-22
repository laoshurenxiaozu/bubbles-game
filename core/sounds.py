"""
Sound manager for Bubbles game.
Handles loading, playback, and volume control for all sound effects.
"""

import pygame
from pathlib import Path


SOUNDS_DIR = Path(__file__).resolve().parents[1] / "assets" / "sounds"


# Mapping of sound names to their filenames
SOUND_FILES = {
    "bubble_collect": "bubble_collect.wav",
    "seed_collect": "seed_collect.wav",
    "bubble_burst": "bubble_burst.wav",
    "bubble_split": "bubble_split.wav",
    "seed_release": "seed_release.wav",
    "level_complete": "level_complete.wav",
    "player_death": "player_death.wav",
    "menu_select": "menu_select.wav",
    "menu_move": "menu_move.wav",
    "bubble_spawn": "bubble_spawn.wav",
    "leaf_touch": "leaf_touch.wav",
    "transition": "transition.wav",
    "pause_in": "pause_in.wav",
    "pause_out": "pause_out.wav",
}


SOUND_PROFILES = {
    "menu_move": {"gain": 0.42, "cooldown": 0.045, "layer": "feedback"},
    "menu_select": {"gain": 0.55, "cooldown": 0.035, "layer": "feedback"},
    "bubble_spawn": {"gain": 0.52, "cooldown": 0.16, "layer": "feedback"},
    "leaf_touch": {"gain": 0.55, "cooldown": 0.18, "layer": "feedback"},
    "bubble_collect": {"gain": 0.62, "cooldown": 0.045, "layer": "feedback"},
    "bubble_split": {"gain": 0.68, "cooldown": 0.08, "layer": "feedback"},
    "seed_release": {"gain": 0.64, "cooldown": 0.08, "layer": "feedback"},
    "bubble_burst": {"gain": 0.70, "cooldown": 0.10, "layer": "event"},
    "seed_collect": {"gain": 0.78, "cooldown": 0.06, "layer": "event"},
    "pause_in": {"gain": 0.48, "cooldown": 0.08, "layer": "feedback"},
    "pause_out": {"gain": 0.48, "cooldown": 0.08, "layer": "feedback"},
    "transition": {"gain": 0.60, "cooldown": 0.20, "layer": "event"},
    "level_complete": {"gain": 0.82, "cooldown": 0.35, "layer": "event"},
    "player_death": {"gain": 0.86, "cooldown": 0.35, "layer": "event"},
}


class SoundManager:
    """Manages all sound effects for the game.

    Uses pygame.mixer for playback. Call init() after pygame.init().
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._sounds = {}
            cls._instance._sfx_volume = 80
            cls._instance._last_played = {}
        return cls._instance

    def init(self, sfx_volume=80):
        """Initialize the mixer and load all sound files.

        Must be called after pygame.init(). Safe to call multiple times.
        """
        if self._initialized:
            self.set_sfx_volume(sfx_volume)
            return

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error:
            print("[SoundManager] Warning: Could not initialize audio mixer. Sound disabled.")
            self._initialized = True
            self._sounds = {}
            self._sfx_volume = sfx_volume
            return

        self._sounds = {}
        self._sfx_volume = sfx_volume

        for name, filename in SOUND_FILES.items():
            path = SOUNDS_DIR / filename
            if path.exists():
                try:
                    self._sounds[name] = pygame.mixer.Sound(str(path))
                except pygame.error:
                    print(f"[SoundManager] Warning: Could not load {filename}")
            else:
                print(f"[SoundManager] Warning: Missing sound file: {path}")

        self.set_sfx_volume(sfx_volume)
        self._initialized = True
        print(f"[SoundManager] Loaded {len(self._sounds)} sound effects")

    def play(self, name):
        """Play a sound effect by name. Fails silently if sound not found."""
        if not self._initialized:
            return
        if self.is_on_cooldown(name):
            return
        sound = self._sounds.get(name)
        if sound:
            self._last_played[name] = pygame.time.get_ticks()
            sound.play()

    def is_on_cooldown(self, name):
        cooldown = SOUND_PROFILES.get(name, {}).get("cooldown", 0.0)
        if cooldown <= 0:
            return False
        previous = self._last_played.get(name)
        if previous is None:
            return False
        return pygame.time.get_ticks() - previous < cooldown * 1000

    def set_sfx_volume(self, volume):
        """Set volume for all sound effects (0-100)."""
        self._sfx_volume = max(0, min(100, volume))
        if not getattr(self, "_initialized", False):
            return
        self.apply_volumes()

    def apply_volumes(self):
        for name, sound in getattr(self, "_sounds", {}).items():
            profile = SOUND_PROFILES.get(name, {})
            gain = profile.get("gain", 1.0)
            volume = self._sfx_volume / 100.0
            sound.set_volume(volume * gain)

    def get_sfx_volume(self):
        """Get current SFX volume (0-100)."""
        return getattr(self, "_sfx_volume", 80)

    def has_sound(self, name):
        """Check if a sound effect is loaded."""
        if not getattr(self, "_initialized", False):
            return False
        return name in self._sounds
