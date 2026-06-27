import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.merge_system import BubbleMergeSystem
from entities.objects import DroppedSeed, FreeBubble


class RecordingSound:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


class MergeSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def build_world(self):
        return SimpleNamespace(
            player=None,
            wild_seeds=[],
            free_bubbles=[],
            dropped_seeds=[],
            fusion_bubbles=[],
            burst_effects=[],
            sound=RecordingSound(),
        )

    def test_two_dropped_seeds_do_not_merge(self):
        first = DroppedSeed(100, 100)
        second = DroppedSeed(100, 100)

        self.assertFalse(
            BubbleMergeSystem.can_merge_pair(first, second)
        )

    def test_overlapping_bubble_and_seed_create_fusion_body(self):
        world = self.build_world()
        world.free_bubbles.append(FreeBubble(100, 100))
        world.dropped_seeds.append(DroppedSeed(100, 100))
        system = BubbleMergeSystem(world)

        system.resolve()

        self.assertEqual(1, len(world.fusion_bubbles))
        fusion = world.fusion_bubbles[0]
        self.assertEqual(1, fusion.bubble_count)
        self.assertEqual(1, fusion.seed_count)
        self.assertEqual([], world.free_bubbles)
        self.assertEqual([], world.dropped_seeds)

    def test_two_fusion_bodies_spill_one_free_bubble(self):
        first = SimpleNamespace(
            x=10,
            y=20,
            bubble_count=2,
            seed_count=1,
        )
        second = SimpleNamespace(
            x=30,
            y=40,
            bubble_count=1,
            seed_count=2,
        )
        system = BubbleMergeSystem(self.build_world())

        result = system.pair_merge_result(first, second)

        self.assertEqual((20, 30, 2, 3, True), result)


if __name__ == "__main__":
    unittest.main()
