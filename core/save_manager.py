import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


class SaveManager:
    SLOT_COUNT = 3

    def __init__(self, save_path=None):
        self.save_path = Path(save_path) if save_path else Path(__file__).resolve().parent.parent / "save_slots.json"
        self.data = self.load()

    def default_data(self):
        return {
            "last_slot": None,
            "slots": [None for _ in range(self.SLOT_COUNT)],
        }

    def load(self):
        if not self.save_path.exists():
            return self.default_data()
        try:
            data = json.loads(self.save_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.default_data()

        slots = data.get("slots", [])
        normalized_slots = []
        for index in range(self.SLOT_COUNT):
            normalized_slots.append(slots[index] if index < len(slots) else None)
        return {
            "last_slot": data.get("last_slot"),
            "slots": normalized_slots,
        }

    def persist(self):
        self.save_path.write_text(
            json.dumps(self.data, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def get_slot(self, slot_index):
        if not 0 <= slot_index < self.SLOT_COUNT:
            return None
        slot = self.data["slots"][slot_index]
        return deepcopy(slot) if slot else None

    def save_slot(self, slot_index, snapshot):
        if not 0 <= slot_index < self.SLOT_COUNT:
            raise ValueError("Invalid slot index")

        payload = deepcopy(snapshot)
        payload["slot_index"] = slot_index
        payload["saved_at"] = datetime.now(timezone.utc).isoformat()
        self.data["slots"][slot_index] = payload
        self.data["last_slot"] = slot_index
        self.persist()
