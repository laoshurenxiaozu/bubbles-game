import unittest

import pygame

from entities.objects import DroppedSeed, FreeBubble


class WallStub:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)


class FloatBodyWallCollisionTest(unittest.TestCase):
    def test_sinking_seed_catches_wall_even_if_frame_steps_past_it(self):
        seed = DroppedSeed(50, 130)
        wall = WallStub((20, 100, 80, 20))

        seed.resolve_vertical_wall_collisions([wall], previous_y=80)

        self.assertEqual(wall.rect.top - seed.radius, seed.y)

    def test_sinking_seed_embedded_in_wall_is_pushed_back_to_top(self):
        seed = DroppedSeed(50, 104)
        wall = WallStub((20, 100, 80, 20))

        seed.resolve_vertical_wall_collisions([wall], previous_y=104)

        self.assertEqual(wall.rect.top - seed.radius, seed.y)

    def test_rising_bubble_catches_wall_even_if_frame_steps_past_it(self):
        bubble = FreeBubble(50, 80)
        wall = WallStub((20, 100, 80, 20))

        bubble.resolve_vertical_wall_collisions([wall], previous_y=140)

        self.assertEqual(wall.rect.bottom + bubble.radius, bubble.y)


if __name__ == "__main__":
    unittest.main()
