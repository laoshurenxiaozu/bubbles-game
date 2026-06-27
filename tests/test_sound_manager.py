import unittest

from core.sounds import SoundManager


class SoundManagerTest(unittest.TestCase):
    def setUp(self):
        SoundManager._instance = None

    def test_music_volume_uses_lower_output_gain(self):
        sound = SoundManager()

        sound.set_music_volume(80)

        self.assertEqual(80, sound.get_music_volume())
        self.assertAlmostEqual(0.30, sound.music_output_volume())


if __name__ == "__main__":
    unittest.main()
