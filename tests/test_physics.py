import unittest

import pygame

from entities.objects import DroppedSeed, FreeBubble, Spike
from entities.player import Player


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


class PlayerCircleCollisionTest(unittest.TestCase):
    def test_player_does_not_collide_with_wall_corner_outside_circle(self):
        player = Player((78, 78))
        player.previous_x = 60
        player.previous_y = 78
        wall = WallStub((100, 100, 40, 40))

        player.resolve_wall_collisions([wall])

        self.assertEqual(78, player.x)
        self.assertEqual(78, player.y)

    def test_player_circle_catches_wall_face(self):
        player = Player((120, 80))
        player.previous_x = 120
        player.previous_y = 60
        wall = WallStub((100, 100, 40, 40))

        player.resolve_wall_collisions([wall])

        self.assertEqual(wall.rect.top - player.radius, player.y)

    def test_spike_ignores_player_rect_corner_outside_circle(self):
        spike = Spike(100, 100, width=40, height=30, direction="down")

        self.assertFalse(spike.collides_with_circle((92, 92), 10))

    def test_spike_detects_player_circle_touching_tip(self):
        spike = Spike(100, 100, width=40, height=30, direction="down")

        self.assertTrue(spike.collides_with_circle((120, 140), 13))


if __name__ == "__main__":
    unittest.main()
