from levels.level_data import LEVEL_DEFINITIONS


DEFAULT_REGION = "nursery"
THORN_REEF_REGION = "thorn_reef"

REGION_DISPLAY_NAMES = {
    DEFAULT_REGION: "初生海",
    THORN_REEF_REGION: "荆棘礁",
}

REQUIRED_LEVEL_FIELDS = {
    "name",
    "display_name",
    "map_label",
    "description",
    "region",
}


def validate_level_definitions():
    names = set()
    for index, definition in enumerate(LEVEL_DEFINITIONS):
        missing = REQUIRED_LEVEL_FIELDS - definition.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"Level {index} is missing catalog fields: {fields}")
        name = definition["name"]
        if name in names:
            raise ValueError(f"Duplicate level name: {name}")
        names.add(name)


def level_count():
    return len(LEVEL_DEFINITIONS)


def level_indices_for_region(region):
    return [
        index
        for index, definition in enumerate(LEVEL_DEFINITIONS)
        if definition["region"] == region
    ]


def first_level_index(region):
    indices = level_indices_for_region(region)
    if not indices:
        raise ValueError(f"Region has no levels: {region}")
    return indices[0]


def last_level_index(region):
    indices = level_indices_for_region(region)
    if not indices:
        raise ValueError(f"Region has no levels: {region}")
    return indices[-1]


def level_region(level_index):
    return LEVEL_DEFINITIONS[level_index]["region"]


def level_internal_name(level_index):
    return LEVEL_DEFINITIONS[level_index]["name"]


def level_map_label(level_index):
    return LEVEL_DEFINITIONS[level_index]["map_label"]


def level_description(level_index):
    return LEVEL_DEFINITIONS[level_index]["description"]


def level_tabs():
    return [
        (definition["map_label"], index)
        for index, definition in enumerate(LEVEL_DEFINITIONS)
    ]


def level_descriptions():
    return [definition["description"] for definition in LEVEL_DEFINITIONS]


def display_level_name(internal_name):
    if internal_name == "Empty":
        return "空"
    for definition in LEVEL_DEFINITIONS:
        if definition["name"] == internal_name:
            return definition["display_name"]
    return internal_name


def region_display_name(region):
    return REGION_DISPLAY_NAMES.get(region, region)


validate_level_definitions()
