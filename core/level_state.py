from config import BUBBLE_VENT_SPAWN_INTERVAL
from entities.objects import (
    BubbleVent,
    DroppedSeed,
    FreeBubble,
    FusionBubble,
    WildSeed,
)


class LevelStateCodec:
    def __init__(self, world):
        self.world = world

    @staticmethod
    def normalize_keys(state_map):
        normalized = {}
        for key, value in state_map.items():
            try:
                normalized[int(key)] = value
            except (TypeError, ValueError):
                continue
        return normalized

    def restore(self, saved_state):
        world = self.world
        world.wild_seeds = [
            WildSeed(seed["x"], seed["y"])
            for seed in saved_state.get("wild_seeds", [])
        ]
        for seed, data in zip(
            world.wild_seeds,
            saved_state.get("wild_seeds", []),
        ):
            seed.collected = data.get("collected", False)

        world.free_bubbles = [
            self.build_free_bubble(data)
            for data in saved_state.get("free_bubbles", [])
        ]
        world.dropped_seeds = [
            self.build_dropped_seed(data)
            for data in saved_state.get("dropped_seeds", [])
        ]
        world.fusion_bubbles = [
            self.build_fusion_bubble(data)
            for data in saved_state.get("fusion_bubbles", [])
        ]
        world.level_souvenirs = [
            self.build_souvenir(data)
            for data in saved_state.get("souvenirs", [])
        ]

    def snapshot(self):
        world = self.world
        return {
            "wild_seeds": [
                {
                    "x": seed.x,
                    "y": seed.y,
                    "collected": seed.collected,
                }
                for seed in world.wild_seeds
            ],
            "free_bubbles": [
                {
                    "x": bubble.x,
                    "y": bubble.y,
                    "collected": bubble.collected,
                    "pickup_delay": bubble.pickup_delay,
                    "bubble_count": bubble.bubble_count,
                    "seed_count": bubble.seed_count,
                    "fusion_lock": bubble.fusion_lock,
                }
                for bubble in world.free_bubbles
            ],
            "dropped_seeds": [
                {
                    "x": seed.x,
                    "y": seed.y,
                    "collected": seed.collected,
                    "bubble_count": seed.bubble_count,
                    "seed_count": seed.seed_count,
                    "fusion_lock": seed.fusion_lock,
                }
                for seed in world.dropped_seeds
            ],
            "fusion_bubbles": [
                {
                    "x": bubble.x,
                    "y": bubble.y,
                    "bubble_count": bubble.bubble_count,
                    "seed_count": bubble.seed_count,
                    "fusion_lock": bubble.fusion_lock,
                }
                for bubble in world.fusion_bubbles
            ],
            "souvenirs": [
                {
                    "kind": (
                        "seed"
                        if isinstance(obj, DroppedSeed)
                        else "bubble"
                    ),
                    "x": obj.x,
                    "y": obj.y,
                }
                for obj in world.level_souvenirs
            ],
        }

    @staticmethod
    def build_free_bubble(data):
        bubble = FreeBubble(
            data["x"],
            data["y"],
            pickup_delay=data.get("pickup_delay", 0.0),
        )
        bubble.collected = data.get("collected", False)
        bubble.bubble_count = data.get(
            "bubble_count",
            bubble.bubble_count,
        )
        bubble.seed_count = data.get(
            "seed_count",
            bubble.seed_count,
        )
        bubble.fusion_lock = data.get(
            "fusion_lock",
            bubble.fusion_lock,
        )
        return bubble

    @staticmethod
    def build_dropped_seed(data):
        seed = DroppedSeed(data["x"], data["y"])
        seed.collected = data.get("collected", False)
        seed.bubble_count = data.get(
            "bubble_count",
            seed.bubble_count,
        )
        seed.seed_count = data.get(
            "seed_count",
            seed.seed_count,
        )
        seed.fusion_lock = data.get(
            "fusion_lock",
            seed.fusion_lock,
        )
        return seed

    @staticmethod
    def build_fusion_bubble(data):
        bubble = FusionBubble(
            data["x"],
            data["y"],
            bubble_count=data.get("bubble_count", 1),
            seed_count=data.get("seed_count", 1),
        )
        bubble.fusion_lock = data.get(
            "fusion_lock",
            bubble.fusion_lock,
        )
        return bubble

    @staticmethod
    def build_bubble_vent(data):
        if isinstance(data, dict):
            x = data["x"]
            y = data["y"]
            spawn_interval = data.get(
                "spawn_interval",
                BUBBLE_VENT_SPAWN_INTERVAL,
            )
        else:
            x, y = data
            spawn_interval = BUBBLE_VENT_SPAWN_INTERVAL
        return BubbleVent(
            x,
            y,
            spawn_interval=spawn_interval,
        )

    @staticmethod
    def build_souvenir(data):
        if data.get("kind") == "seed":
            return DroppedSeed(data["x"], data["y"])
        return FreeBubble(data["x"], data["y"])
