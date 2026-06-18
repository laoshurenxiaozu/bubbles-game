import unittest

from core.game import Game
from core.save_manager import SaveManager


class SaveDirtyTest(unittest.TestCase):
    def make_game_with_slots(self, slots):
        game = Game.__new__(Game)
        game.save_manager = SaveManager("unused_save_slots.json")
        game.save_manager.data = {
            "last_slot": 0,
            "slots": slots,
        }
        return game

    def test_saved_progress_is_not_dirty_when_slot_index_only_exists_in_session(self):
        saved = {
            "current_level_index": 1,
            "latest_level_index": 0,
            "unlocked_levels": 1,
            "player_bubbles": 1,
            "player_seeds": 2,
            "seed_total": 2,
            "completed_level_states": {},
            "stars_by_level": {"0": 3},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
        }
        progress = {
            **saved,
            "slot_index": 0,
            "has_started_game": True,
        }
        game = self.make_game_with_slots([saved, None, None])

        self.assertFalse(game.compute_session_dirty(progress))

    def test_changed_saved_progress_is_dirty(self):
        saved = {
            "current_level_index": 1,
            "latest_level_index": 0,
            "unlocked_levels": 1,
            "player_bubbles": 1,
            "player_seeds": 2,
            "seed_total": 2,
            "completed_level_states": {},
            "stars_by_level": {},
            "current_region": "nursery",
            "thorn_reef_unlocked": False,
        }
        progress = {
            **saved,
            "slot_index": 0,
            "has_started_game": True,
            "player_seeds": 3,
            "seed_total": 3,
        }
        game = self.make_game_with_slots([saved, None, None])

        self.assertTrue(game.compute_session_dirty(progress))

    def test_unslotted_progress_is_dirty(self):
        game = self.make_game_with_slots([None, None, None])

        self.assertTrue(game.compute_session_dirty({"has_started_game": True, "slot_index": None}))


if __name__ == "__main__":
    unittest.main()
