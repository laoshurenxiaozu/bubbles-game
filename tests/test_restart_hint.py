import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ui.restart_hint import RestartHintOverlay


class RestartHintOverlayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.overlay = RestartHintOverlay(pygame.font.Font(None, 20))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_motion_phases_are_ordered(self):
        motion = self.overlay.motion((480, 300), 39)

        self.assertLess(motion["rise_start"], motion["seed_start"])
        self.assertLess(motion["seed_start"], motion["capture_t"])
        self.assertLess(motion["capture_t"], motion["landing_t"])
        self.assertLess(motion["landing_t"], motion["seed_ground_t"])
        self.assertLess(motion["seed_ground_t"], motion["leaf_start"])

    def test_partial_polyline_preserves_requested_fraction(self):
        points = [(0, 0), (10, 0), (20, 0)]

        partial = self.overlay.partial_polyline(points, 0.75)

        self.assertEqual([(0, 0), (10, 0), (15, 0)], partial)

    def test_representative_animation_frames_render(self):
        for elapsed in (0.0, 2.6, 3.7, 5.5, 7.0):
            surface = pygame.Surface((960, 540), pygame.SRCALPHA)

            self.overlay.draw(
                surface,
                elapsed=elapsed,
                duration=7.4,
                text="重开提示",
                world_time=elapsed,
            )

            self.assertGreater(surface.get_at((480, 270)).a, 0)

    def test_fade_layer_changes_rendered_frame(self):
        plain = pygame.Surface((960, 540), pygame.SRCALPHA)
        faded = pygame.Surface((960, 540), pygame.SRCALPHA)

        self.overlay.draw(
            plain,
            elapsed=7.4,
            duration=7.4,
            text="重开提示",
            world_time=7.4,
        )
        self.overlay.draw(
            faded,
            elapsed=7.4,
            duration=7.4,
            text="重开提示",
            world_time=7.4,
            fading=True,
            fade_time=0.18,
            fade_duration=0.35,
        )

        self.assertNotEqual(plain.get_at((0, 0)), faded.get_at((0, 0)))


if __name__ == "__main__":
    unittest.main()
