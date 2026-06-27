from levels.catalog import display_level_name


class SaveFlowMixin:
    SAVE_SLOT_COUNT = 3

    def current_save_slot_index(self):
        raise NotImplementedError

    def default_save_name(self, slot_index):
        return f"存档 {slot_index + 1}"

    def slot_display_name(self, slot_index):
        if slot_index is None:
            return self.default_save_name(0)
        slot = (
            self.save_manager.get_slot(slot_index)
            if self.save_manager
            else None
        )
        if slot and slot.get("name"):
            return slot["name"]
        return self.default_save_name(slot_index)

    def save_action_options(self):
        if self.current_save_slot_index() is None:
            return [("另存为新存档", "save_as_new")]
        return [
            ("覆盖当前存档", "update_current"),
            ("另存为新存档", "save_as_new"),
        ]

    def reset_save_flow(self):
        current_slot_index = self.current_save_slot_index()
        self.save_message = ""
        self.save_editing = False
        self.save_cursor_timer = 0.0
        self.save_action_index = 0
        self.save_forbid_current_slot = current_slot_index is not None
        if current_slot_index is None:
            self.save_flow = "choose_slot"
            self.save_slot_index = 0
        else:
            self.save_flow = "choose_action"
            self.save_slot_index = current_slot_index
        self.save_name_input = self.slot_display_name(
            self.save_slot_index
        )

    def move_save_slot_selection(self, delta):
        current_slot_index = self.current_save_slot_index()
        available_slots = list(range(self.SAVE_SLOT_COUNT))
        if (
            self.save_forbid_current_slot
            and current_slot_index is not None
        ):
            available_slots.remove(current_slot_index)
        if not available_slots:
            return
        current = (
            self.save_slot_index
            if self.save_slot_index in available_slots
            else available_slots[0]
        )
        index = available_slots.index(current)
        self.save_slot_index = available_slots[
            (index + delta) % len(available_slots)
        ]
        self.save_name_input = self.slot_display_name(
            self.save_slot_index
        )
        self.save_message = ""

    def begin_save_name_edit(self):
        self.save_editing = True
        self.save_name_input = ""
        self.save_message = "输入名称后，再按回车保存"
        self.save_cursor_timer = 0.0

    def prepare_save_as_new(self):
        current_slot_index = self.current_save_slot_index()
        self.save_flow = "choose_slot"
        self.save_forbid_current_slot = current_slot_index is not None
        self.save_slot_index = (
            0
            if current_slot_index is None
            else (current_slot_index + 1) % self.SAVE_SLOT_COUNT
        )
        if self.is_save_slot_locked(self.save_slot_index):
            self.move_save_slot_selection(1)
        self.save_name_input = self.slot_display_name(
            self.save_slot_index
        )
        self.save_message = ""

    def is_save_slot_locked(self, slot_index):
        current_slot_index = self.current_save_slot_index()
        return (
            self.save_forbid_current_slot
            and current_slot_index is not None
            and slot_index == current_slot_index
        )

    def select_save_slot(
        self,
        slot_index,
        begin_edit_on_repeat=False,
    ):
        if self.is_save_slot_locked(slot_index):
            return
        already_selected = self.save_slot_index == slot_index
        self.save_slot_index = slot_index
        if self.save_editing:
            return
        if begin_edit_on_repeat and already_selected:
            self.begin_save_name_edit()
        else:
            self.save_name_input = self.slot_display_name(slot_index)
            self.save_message = ""

    def save_slot_summary(self, slot_index):
        slot = (
            self.save_manager.get_slot(slot_index)
            if self.save_manager
            else None
        )
        if not slot:
            return self.default_save_name(slot_index), "空", 0
        return (
            slot.get("name") or self.default_save_name(slot_index),
            display_level_name(
                slot.get("latest_level_name", "Empty")
            ),
            slot.get("seed_total", 0),
        )

    def display_level_name(self, level_name):
        return display_level_name(level_name)
