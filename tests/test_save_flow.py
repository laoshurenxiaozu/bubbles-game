import unittest

from core.save_flow import SaveFlowMixin


class FakeSaveManager:
    def __init__(self):
        self.slots = [
            {"name": "Primary", "latest_level_name": "Tutorial1"},
            None,
            None,
        ]

    def get_slot(self, index):
        return self.slots[index]


class FakeSaveFlow(SaveFlowMixin):
    def __init__(self, current_slot_index):
        self.save_manager = FakeSaveManager()
        self.current_slot = current_slot_index
        self.save_slot_index = 0
        self.save_forbid_current_slot = False
        self.save_editing = False
        self.save_name_input = ""
        self.save_message = ""
        self.save_cursor_timer = 0.0
        self.save_action_index = 0
        self.save_flow = "choose_action"

    def current_save_slot_index(self):
        return self.current_slot


class SaveFlowTest(unittest.TestCase):
    def test_unsaved_progress_starts_with_slot_selection(self):
        flow = FakeSaveFlow(None)

        flow.reset_save_flow()

        self.assertEqual("choose_slot", flow.save_flow)
        self.assertEqual(0, flow.save_slot_index)
        self.assertFalse(flow.save_forbid_current_slot)

    def test_existing_save_starts_with_action_selection(self):
        flow = FakeSaveFlow(0)

        flow.reset_save_flow()

        self.assertEqual("choose_action", flow.save_flow)
        self.assertEqual("Primary", flow.save_name_input)
        self.assertTrue(flow.save_forbid_current_slot)

    def test_save_as_new_skips_current_slot(self):
        flow = FakeSaveFlow(0)

        flow.prepare_save_as_new()

        self.assertEqual("choose_slot", flow.save_flow)
        self.assertEqual(1, flow.save_slot_index)
        self.assertTrue(flow.is_save_slot_locked(0))

    def test_selecting_same_slot_twice_begins_name_edit(self):
        flow = FakeSaveFlow(None)
        flow.reset_save_flow()

        flow.select_save_slot(0, begin_edit_on_repeat=True)

        self.assertTrue(flow.save_editing)
        self.assertEqual("", flow.save_name_input)


if __name__ == "__main__":
    unittest.main()
