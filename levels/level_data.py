from copy import deepcopy


LEVEL_DEFINITIONS = [
    {
        # Level1: Learn dive/surface & A/D horizontal movement
        "name": "Tutorial1",
        "display_name": "教程一",
        "map_label": "初生海 - 1",
        "description": "学习泡泡的移动路线，抵达安全的叶子。",
        "region": "nursery",
        "start_leaf": (78, 235, 82, 46),
        "goal_leaf": (514, 458, 92, 52),
        "player_spawn": (118, 258),
        "walls": [],
        "spikes": [],
        "wild_seeds": [
            (310, 160),
            (766, 160),
        ],
        "free_bubbles": [],
        "bubble_vents": [],
        "pollution_zones": [],
        "intro": True,
    },
    {
        # Level2: Learn W to spit seeds and adjust buoyancy
        "name": "Tutorial2",
        "display_name": "教程二",
        "map_label": "初生海 - 2",
        "description": "练习释放种子，并在开阔水域收集自由泡泡。",
        "region": "nursery",
        "start_leaf": (88, 70, 82, 46),
        "goal_leaf": (804, 195, 92, 52),
        "player_spawn": (120, 124),
        "walls": [],
        "spikes": [],
        "wild_seeds": [],
        "free_bubbles": [
            {
                "x": 350,
                "y": 512,
                "trigger": "move",
                "refresh": True,
            },
        ],
        "bubble_vents": [],
        "pollution_zones": [],
        "intro": False,
    },
    {
        # Level3: Learn spikes, walls & S to split bubbles and adjust buoyancy
        "name": "Tutorial3",
        "display_name": "教程三",
        "map_label": "初生海 - 3",
        "description": "穿过墙体和尖刺，用分裂泡泡调整浮力。",
        "region": "nursery",
        "start_leaf": (58, 448, 82, 46),
        "goal_leaf": (820, 430, 92, 52),
        "player_spawn": (112, 466),
        "walls": [
            (0, 376, 270, 24),
            (552, 128, 362, 26),
            (748, 300, 28, 208),
        ],
        "spikes": [
            (604, 152, "down"),
            (638, 152, "down"),
            (672, 152, "down"),
            (706, 152, "down"),
            (715, 304, "left"),
            (715, 338, "left"),
            (715, 372, "left"),
            (715, 406, "left"),
            (118, 400, "down"),
            (152, 400, "down"),
            (186, 400, "down"),
        ],
        "wild_seeds": [
            (474, 350),
            (892, 250),
        ],
        "free_bubbles": [
            {
                "x": 300,
                "y": 518,
                "trigger": "move",
                "refresh": True,
            },
        ],
        "bubble_vents": [],
        "pollution_zones": [],
        "intro": False,
    },
    {
        # Level4: Learn bubble vents & store seeds temporarily
        "name": "Tutorial4",
        "display_name": "教程四",
        "map_label": "初生海 - 4",
        "description": "利用气泡喷口补充泡泡，同时保留足够的种子。",
        "region": "nursery",
        "start_leaf": (26, 148, 82, 46),
        "goal_leaf": (786, 84, 92, 52),
        "player_spawn": (84, 176),
        "walls": [
            (218, 30, 180, 28),
            (676, 214, 284, 28),
            (458, 488, 260, 28),
            (676, 30, 200, 28),
        ],
        "spikes": [
            (240, 56, "down"),
            (274, 56, "down"),
            (308, 56, "down"),
            (342, 56, "down"),
            (750, 242, "down"),
            (784, 242, "down"),
            (818, 242, "down"),
            (852, 242, "down"),
            (484, 460, "up"),
            (518, 460, "up"),
            (552, 460, "up"),
            (586, 460, "up"),
            (620, 460, "up"),
            (654, 460, "up"),
            (690, 56, "down"),
            (724, 56, "down"),
        ],
        "wild_seeds": [],
        "free_bubbles": [],
        "bubble_vents": [
            {"x": 316, "y": 538, "spawn_interval": 1.4},
            {"x": 818, "y": 538, "spawn_interval": 2.0},
        ],
        "dropped_seeds": [
            (610, 38),
        ],
        "pollution_zones": [],
        "intro": False,
    },
    {
        # Level5: Leave the shared start/goal leaf and return with life
        "name": "Reef1",
        "display_name": "荆棘礁一",
        "map_label": "荆棘礁 - 1",
        "description": "带着初始泡泡与种子离开叶片，绕过尖刺后返回原点。",
        "region": "thorn_reef",
        "start_leaf": (140, 276, 82, 46),
        "goal_leaf": (140, 276, 82, 46),
        "player_spawn": (210, 300),
        "goal_at_start": True,
        "goal_return_delay": 1.0,
        "walls": [
            (214, 52, 130, 34),
        ],
        "spikes": [
            (228, 86, "down"),
            (262, 86, "down"),
            (296, 86, "down"),
        ],
        "wild_seeds": [
            (830, 100)
        ],
        "free_bubbles": [
            {
                "x": 263,
                "y": 527,
                "refresh": True,
            },
        ],
        "dropped_seeds": [
            {
                "x": 650,
                "y": 8,
                "delay": 2.0,
            },
        ],
        "bubble_vents": [],
        "pollution_zones": [],
        "intro": False,
    },
    {
        # Level6: Use bubble vents to navigate beneath hanging spikes
        "name": "Reef2",
        "display_name": "荆棘礁二",
        "map_label": "荆棘礁 - 2",
        "description": "借助气泡喷口穿行于悬垂尖刺之间，收集种子后返回叶片。",
        "region": "thorn_reef",
        "start_leaf": (40, 270, 82, 46),
        "goal_leaf": (40, 270, 82, 46),
        "player_spawn": (90, 310),
        "goal_at_start": True,
        "goal_return_delay": 1.0,
        "walls": [
            (356, 430, 330, 30),
            (790, 270, 150, 30),
            (790, 50, 30, 135),
        ],
        "spikes": [
            (378, 402, "up"),
            (412, 402, "up"),
            (446, 402, "up"),
            (480, 402, "up"),
            (378, 460, "down"),
            (412, 460, "down"),
            (446, 460, "down"),
            (480, 460, "down"),
            (816, 300, "down"),
            (850, 300, "down"),
            (884, 300, "down"),
            (685, 430, "right"),
        ],
        "wild_seeds": [
            (590, 500),
            (884, 100),
        ],
        "free_bubbles": [],
        "dropped_seeds": [
            {
                "x": 590,
                "y": 8,
                "delay": 1.0,
            },
        ],
        "bubble_vents": [
            {"x": 590, "y": 430, "spawn_interval": 1.1, "first_spawn_delay": 0},
            {"x": 866, "y": 538},
        ],
        "pollution_zones": [],
        "intro": False,
    },
]


def build_levels():
    return deepcopy(LEVEL_DEFINITIONS)
