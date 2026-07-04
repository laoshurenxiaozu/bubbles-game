import unittest

from ui.widgets import ControlHintVisibility


class ControlHintVisibilityTest(unittest.TestCase):
    def test_hint_fades_after_three_seconds_and_returns_on_hover(self):
        visibility = ControlHintVisibility(
            duration=3.0,
            fade_duration=0.5,
            reentry_gap=100.0,
        )

        self.assertEqual(255, visibility.opacity("menu", 0.0))
        self.assertEqual(255, visibility.opacity("menu", 3.0))
        self.assertGreater(visibility.opacity("menu", 3.25), 0)
        self.assertEqual(0, visibility.opacity("menu", 3.5))
        self.assertEqual(
            255,
            visibility.opacity("menu", 3.6, hovered=True),
        )
        self.assertEqual(0, visibility.opacity("menu", 3.7))

    def test_hint_restarts_for_new_context_or_reentry(self):
        visibility = ControlHintVisibility(
            duration=5.0,
            fade_duration=0.0,
            reentry_gap=0.75,
        )

        visibility.opacity("menu", 0.0)
        self.assertEqual(255, visibility.opacity("settings", 0.1))
        for step in range(1, 53):
            opacity = visibility.opacity("settings", step / 10)
        self.assertEqual(0, opacity)
        self.assertEqual(255, visibility.opacity("settings", 6.1))

    def test_hint_enabled_state_can_change_at_runtime(self):
        state = {"enabled": True}
        visibility = ControlHintVisibility(
            enabled=lambda: state["enabled"]
        )

        self.assertTrue(visibility.is_enabled())
        state["enabled"] = False
        self.assertFalse(visibility.is_enabled())


if __name__ == "__main__":
    unittest.main()
