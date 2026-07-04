import unittest

from core.level_state import LevelStateCodec
from entities.objects import BubbleVent


class BubbleVentTest(unittest.TestCase):
    def test_first_spawn_delay_only_controls_first_bubble(self):
        vent = BubbleVent(
            100,
            200,
            spawn_interval=1.0,
            first_spawn_delay=0.25,
        )

        self.assertFalse(vent.update(0.2))
        self.assertTrue(vent.update(0.1))
        self.assertFalse(vent.update(0.9))
        self.assertTrue(vent.update(0.1))

    def test_first_spawn_defaults_to_regular_interval(self):
        vent = BubbleVent(100, 200, spawn_interval=1.0)

        self.assertFalse(vent.update(0.9))
        self.assertTrue(vent.update(0.1))

    def test_level_data_builds_vent_with_first_spawn_delay(self):
        vent = LevelStateCodec.build_bubble_vent(
            {
                "x": 100,
                "y": 200,
                "spawn_interval": 1.5,
                "first_spawn_delay": 0.4,
            }
        )

        self.assertEqual(1.5, vent.spawn_interval)
        self.assertEqual(0.4, vent.first_spawn_delay)
        self.assertEqual(0.4, vent.timer)


if __name__ == "__main__":
    unittest.main()
