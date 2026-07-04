import unittest
from copy import deepcopy

from levels.catalog import (
    DEFAULT_REGION,
    THORN_REEF_REGION,
    display_level_name,
    level_count,
    level_descriptions,
    level_indices_for_region,
    level_tabs,
    validate_level_definitions,
)
from levels.level_data import LEVEL_DEFINITIONS
from ui.level_map import level_node_centers


class LevelCatalogTest(unittest.TestCase):
    def test_every_level_has_valid_unique_catalog_metadata(self):
        validate_level_definitions()

        names = [definition["name"] for definition in LEVEL_DEFINITIONS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(level_count(), len(level_tabs()))
        self.assertEqual(level_count(), len(level_descriptions()))

    def test_region_indices_come_from_level_definitions(self):
        for region in (DEFAULT_REGION, THORN_REEF_REGION):
            expected = [
                index
                for index, definition in enumerate(LEVEL_DEFINITIONS)
                if definition["region"] == region
            ]
            self.assertEqual(expected, level_indices_for_region(region))

    def test_display_name_uses_catalog_and_preserves_unknown_names(self):
        self.assertEqual("教程一", display_level_name("Tutorial1"))
        self.assertEqual("空", display_level_name("Empty"))
        self.assertEqual("CommunityLevel", display_level_name("CommunityLevel"))

    def test_map_layout_spreads_additional_levels_across_route(self):
        centers = level_node_centers(THORN_REEF_REGION, 6)

        self.assertEqual(6, len(centers))
        self.assertEqual(6, len(set(centers)))

    def test_appending_one_definition_updates_catalog_and_map(self):
        extra = deepcopy(LEVEL_DEFINITIONS[-1])
        extra.update(
            {
                "name": "Reef3",
                "display_name": "荆棘礁三",
                "map_label": "荆棘礁 - 3",
                "description": "目录扩展测试关卡。",
            }
        )
        LEVEL_DEFINITIONS.append(extra)
        try:
            self.assertEqual(
                [4, 5, 6],
                level_indices_for_region(THORN_REEF_REGION),
            )
            self.assertEqual(("荆棘礁 - 3", 6), level_tabs()[-1])
            centers = level_node_centers(
                THORN_REEF_REGION,
                len(level_indices_for_region(THORN_REEF_REGION)),
            )
            self.assertEqual(3, len(set(centers)))
        finally:
            LEVEL_DEFINITIONS.pop()

    def test_first_reef_level_matches_shared_leaf_layout(self):
        reef = LEVEL_DEFINITIONS[4]

        self.assertEqual(reef["start_leaf"], reef["goal_leaf"])
        self.assertTrue(reef["goal_at_start"])
        self.assertEqual(
            0.0,
            reef["free_bubbles"][0].get("delay", 0.0),
        )
        self.assertTrue(reef["free_bubbles"][0]["refresh"])
        self.assertEqual(2.0, reef["dropped_seeds"][0]["delay"])
        self.assertEqual(8, reef["dropped_seeds"][0]["y"])
        self.assertEqual(1, len(reef["walls"]))
        self.assertEqual(3, len(reef["spikes"]))
        self.assertEqual([(830, 100)], reef["wild_seeds"])
        self.assertEqual([], reef["bubble_vents"])

    def test_level_data_uses_unified_object_spawn_fields(self):
        obsolete = {
            "player_bubbles",
            "player_seeds",
            "bubble_spawn",
            "bubble_spawned",
            "initial_dropped_seeds",
            "delayed_wild_seeds",
        }

        for level in LEVEL_DEFINITIONS:
            self.assertTrue(obsolete.isdisjoint(level))

        self.assertTrue(
            LEVEL_DEFINITIONS[1]["free_bubbles"][0]["refresh"]
        )
        self.assertTrue(
            LEVEL_DEFINITIONS[2]["free_bubbles"][0]["refresh"]
        )

    def test_second_reef_level_matches_vent_and_spike_layout(self):
        reef = LEVEL_DEFINITIONS[5]

        self.assertEqual("Reef2", reef["name"])
        self.assertEqual(reef["start_leaf"], reef["goal_leaf"])
        self.assertTrue(reef["goal_at_start"])
        self.assertEqual(3, len(reef["walls"]))
        self.assertEqual(12, len(reef["spikes"]))
        self.assertEqual(
            [
                (378, 402, "up"),
                (412, 402, "up"),
                (446, 402, "up"),
                (480, 402, "up"),
            ],
            reef["spikes"][:4],
        )
        self.assertEqual((685, 430, "right"), reef["spikes"][-1])
        self.assertEqual(
            [(590, 500), (884, 100)],
            reef["wild_seeds"],
        )
        self.assertEqual(1.0, reef["dropped_seeds"][0]["delay"])
        self.assertEqual(2, len(reef["bubble_vents"]))
        self.assertEqual([], reef["free_bubbles"])


if __name__ == "__main__":
    unittest.main()
