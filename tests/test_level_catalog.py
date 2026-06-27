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
                "name": "Reef2",
                "display_name": "荆棘礁二",
                "map_label": "荆棘礁 - 2",
                "description": "目录扩展测试关卡。",
            }
        )
        LEVEL_DEFINITIONS.append(extra)
        try:
            self.assertEqual(
                [4, 5],
                level_indices_for_region(THORN_REEF_REGION),
            )
            self.assertEqual(("荆棘礁 - 2", 5), level_tabs()[-1])
            centers = level_node_centers(
                THORN_REEF_REGION,
                len(level_indices_for_region(THORN_REEF_REGION)),
            )
            self.assertEqual(2, len(set(centers)))
        finally:
            LEVEL_DEFINITIONS.pop()


if __name__ == "__main__":
    unittest.main()
