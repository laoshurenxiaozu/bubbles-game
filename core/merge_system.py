from config import (
    FREE_BUBBLE_RADIUS,
    OBJECT_SPILL_PICKUP_DELAY,
    PLAYER_SPILL_BUBBLE_LIFT,
    PLAYER_SPILL_PICKUP_DELAY,
)
from entities.objects import (
    BurstEffect,
    DroppedSeed,
    FreeBubble,
    FusionBubble,
    WildSeed,
)


class BubbleMergeSystem:
    def __init__(self, world):
        self.world = world

    def resolve(self):
        mergeables = self.collect_mergeables()
        self.resolve_player_merges(mergeables)
        self.resolve_object_merges(mergeables)
        self.prune_collected_objects()

    def resolve_spike_bursts(self, spike):
        world = self.world
        for wild_seed in world.wild_seeds:
            if (
                not wild_seed.collected
                and spike.collides_with(wild_seed.rect)
            ):
                self.burst_fusion_bubble(wild_seed)

        for bubble in world.free_bubbles:
            if (
                not bubble.collected
                and spike.collides_with(bubble.rect)
            ):
                self.burst_bubble_object(bubble)

        for fusion_bubble in world.fusion_bubbles:
            if (
                not fusion_bubble.collected
                and spike.collides_with(fusion_bubble.rect)
            ):
                self.burst_fusion_bubble(fusion_bubble)

    def burst_bubble_object(self, bubble):
        world = self.world
        bubble.collected = True
        bubble.bubble_count = 0
        world.burst_effects.append(
            BurstEffect(bubble.x, bubble.y, bubble.radius)
        )
        world.sound.play("bubble_burst")

    def burst_fusion_bubble(self, fusion_bubble):
        if fusion_bubble.collected:
            return
        world = self.world
        released_seeds = fusion_bubble.seed_count
        self.burst_bubble_object(fusion_bubble)
        fusion_bubble.seed_count = 0
        for index in range(released_seeds):
            offset = (index - (released_seeds - 1) / 2) * 14
            world.dropped_seeds.append(
                DroppedSeed(
                    fusion_bubble.x + offset,
                    fusion_bubble.y,
                )
            )

    def collect_mergeables(self):
        world = self.world
        groups = (
            world.wild_seeds,
            world.free_bubbles,
            world.dropped_seeds,
            world.fusion_bubbles,
        )
        return [
            obj
            for group in groups
            for obj in group
            if not obj.collected
            and getattr(obj, "fusion_lock", 0) <= 0
        ]

    def resolve_player_merges(self, mergeables):
        world = self.world
        if not world.player:
            return
        for obj in mergeables:
            if world.player.rect.colliderect(obj.rect):
                self.merge_player_with(obj)

    def resolve_object_merges(self, mergeables):
        consumed = set()
        for index, first in enumerate(mergeables):
            if id(first) in consumed or first.collected:
                continue
            for second in mergeables[index + 1 :]:
                if id(second) in consumed or second.collected:
                    continue
                if not first.rect.colliderect(second.rect):
                    continue
                if not self.can_merge_pair(first, second):
                    continue
                self.merge_pair(first, second)
                consumed.add(id(first))
                consumed.add(id(second))
                break

    def prune_collected_objects(self):
        world = self.world
        world.wild_seeds = [
            seed
            for seed in world.wild_seeds
            if not seed.collected
        ]
        world.free_bubbles = [
            bubble
            for bubble in world.free_bubbles
            if not bubble.collected
        ]
        world.dropped_seeds = [
            seed
            for seed in world.dropped_seeds
            if not seed.collected
        ]
        world.fusion_bubbles = [
            bubble
            for bubble in world.fusion_bubbles
            if not bubble.collected
        ]

    def merge_player_with(self, obj):
        world = self.world
        spills_bubble = self.is_fusion_body(obj)
        world.player.bubble_count += obj.bubble_count
        world.player.seed_count += obj.seed_count
        obj.collected = True
        if isinstance(obj, (WildSeed, DroppedSeed)):
            world.sound.play("seed_collect")
        else:
            world.sound.play("bubble_collect")
        if spills_bubble:
            world.player.bubble_count = max(
                0,
                world.player.bubble_count - 1,
            )
            spill_x, spill_y = self.player_spill_position(obj)
            self.spill_free_bubble(
                spill_x,
                spill_y,
                pickup_delay=PLAYER_SPILL_PICKUP_DELAY,
            )

    def merge_pair(self, first, second):
        world = self.world
        x, y, bubble_count, seed_count, spills_bubble = (
            self.pair_merge_result(first, second)
        )
        if spills_bubble:
            self.spill_free_bubble(
                x,
                y,
                pickup_delay=OBJECT_SPILL_PICKUP_DELAY,
            )
        world.fusion_bubbles.append(
            FusionBubble(
                x,
                y,
                bubble_count=bubble_count,
                seed_count=seed_count,
            )
        )
        first.collected = True
        second.collected = True

    def pair_merge_result(self, first, second):
        x = (first.x + second.x) / 2
        y = (first.y + second.y) / 2
        bubble_count = first.bubble_count + second.bubble_count
        seed_count = first.seed_count + second.seed_count
        spills_bubble = self.should_spill_bubble(first, second)
        if spills_bubble:
            bubble_count -= 1
        return x, y, bubble_count, seed_count, spills_bubble

    def spill_free_bubble(self, x, y, pickup_delay=0.2):
        self.world.free_bubbles.append(
            FreeBubble(x, y, pickup_delay=pickup_delay)
        )

    def player_spill_position(self, obj):
        world = self.world
        obj_radius = getattr(obj, "radius", 0)
        x = world.player.x
        y = (
            obj.y
            - obj_radius
            - FREE_BUBBLE_RADIUS
            - PLAYER_SPILL_BUBBLE_LIFT
        )
        return x, y

    def should_spill_bubble(self, first, second):
        return (
            self.is_fusion_body(first)
            and self.is_fusion_body(second)
        )

    @staticmethod
    def is_fusion_body(obj):
        return (
            getattr(obj, "bubble_count", 0) > 0
            and getattr(obj, "seed_count", 0) > 0
        )

    @staticmethod
    def can_merge_pair(first, second):
        return not (
            isinstance(first, DroppedSeed)
            and isinstance(second, DroppedSeed)
        )
