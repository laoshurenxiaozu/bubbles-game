from copy import deepcopy

from entities.objects import DroppedSeed, FreeBubble


class LevelObjectSpawner:
    SUPPORTED_TRIGGERS = {"start", "move"}

    def __init__(self, world):
        self.world = world

    def populate(self, level, refresh_only=False):
        if not refresh_only:
            self.world.free_bubbles = []
            self.world.dropped_seeds = []
            self.world.pending_object_spawns = []
        self.add_entries(
            "free_bubble",
            level.get("free_bubbles", []),
            refresh_only=refresh_only,
        )
        self.add_entries(
            "dropped_seed",
            level.get("dropped_seeds", []),
            refresh_only=refresh_only,
        )

    def add_entries(self, kind, entries, refresh_only=False):
        for entry in entries:
            spawn = self.normalize_entry(kind, entry)
            if refresh_only and not spawn["refresh"]:
                continue
            if (
                spawn["trigger"] == "start"
                and spawn["remaining"] <= 0
            ):
                self.spawn(spawn)
            else:
                self.world.pending_object_spawns.append(spawn)

    def update(self, dt, moved=False):
        pending = []
        for spawn in self.world.pending_object_spawns:
            if spawn["trigger"] == "move":
                if not moved:
                    pending.append(spawn)
                    continue
                spawn["trigger"] = "start"

            spawn["remaining"] -= dt
            if spawn["remaining"] > 0:
                pending.append(spawn)
                continue
            self.spawn(spawn)
        self.world.pending_object_spawns = pending

    def spawn(self, spawn):
        if spawn["kind"] == "free_bubble":
            bubble = FreeBubble(
                spawn["x"],
                spawn["y"],
                pickup_delay=spawn.get("pickup_delay", 0.0),
            )
            bubble.refresh_on_reset = spawn.get("refresh", False)
            self.world.free_bubbles.append(bubble)
            return
        seed = DroppedSeed(spawn["x"], spawn["y"])
        seed.refresh_on_reset = spawn.get("refresh", False)
        self.world.dropped_seeds.append(seed)

    def count_pending_seeds(self):
        return sum(
            1
            for spawn in self.world.pending_object_spawns
            if spawn["kind"] == "dropped_seed"
        )

    @classmethod
    def normalize_entry(cls, kind, entry):
        if isinstance(entry, dict):
            data = deepcopy(entry)
        else:
            x, y = entry
            data = {"x": x, "y": y}

        trigger = data.get("trigger", "start")
        if trigger not in cls.SUPPORTED_TRIGGERS:
            raise ValueError(f"Unsupported object spawn trigger: {trigger}")
        spawn = {
            "kind": kind,
            "x": data["x"],
            "y": data["y"],
            "remaining": max(0.0, float(data.get("delay", 0.0))),
            "trigger": trigger,
            "refresh": bool(data.get("refresh", False)),
        }
        if kind == "free_bubble":
            spawn["pickup_delay"] = max(
                0.0,
                float(data.get("pickup_delay", 0.0)),
            )
        return spawn
