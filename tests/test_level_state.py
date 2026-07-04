import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from entities.objects import (
    DroppedSeed,
    FreeBubble,
    FusionBubble,
    WildSeed,
)
from scenes.level_scene import LevelScene


class LevelStateCodecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_snapshot_round_trips_runtime_objects(self):
        source = LevelScene()
        source.wild_seeds = [
            WildSeed(80, 90),
        ]
        source.free_bubbles = [
            FreeBubble(120, 140, pickup_delay=0.25)
        ]
        source.dropped_seeds = [DroppedSeed(220, 240)]
        source.fusion_bubbles = [
            FusionBubble(320, 340, bubble_count=2, seed_count=3)
        ]
        source.level_souvenirs = [DroppedSeed(420, 440)]
        source.pending_object_spawns = [
            {
                "kind": "dropped_seed",
                "x": 500,
                "y": 8,
                "remaining": 1.25,
                "trigger": "start",
                "pickup_delay": 0.0,
            },
        ]
        snapshot = source.snapshot_level_state()

        restored = LevelScene()
        restored.level_state_codec.restore(snapshot)

        self.assertEqual(
            snapshot,
            restored.snapshot_level_state(),
        )

    def test_completed_level_state_keys_accept_json_strings(self):
        scene = LevelScene(
            save_data={
                "completed_level_states": {
                    "0": {"free_bubbles": []},
                    "invalid": {"free_bubbles": []},
                }
            }
        )

        self.assertIn(0, scene.completed_level_states)
        self.assertNotIn("invalid", scene.completed_level_states)

    def test_preview_world_surface_starts_with_opaque_level_background(self):
        scene = LevelScene(level_index=2)

        surface = scene.render_world_surface()

        self.assertFalse(surface.get_flags() & pygame.SRCALPHA)
        self.assertNotEqual((0, 0, 0), surface.get_at((480, 270))[:3])


if __name__ == "__main__":
    unittest.main()
