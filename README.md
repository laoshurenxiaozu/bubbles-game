# Bubbles

A small Pygame prototype for an adventure puzzle game about carrying a life seed inside a bubble.

## Run

Use the Python launcher that matches your system:

- macOS / Linux: `python3`
- Windows: `python`

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

If the `.venv/bin/python` path does not exist on Windows, use:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

## Controls

- `A` / `D` or left / right arrows: move horizontally
- `W` / up arrow: release one collected seed downward
- `S` / down arrow: split off one bubble upward
- `R`: restart the prototype level
- `Esc`: pause

## Current Prototype

- Shared float logic based on `bubble count - seed count`
- The player begins inside a starting leaf, then squeezes out as one floating bubble
- Touching the ending leaf completes the level
- Top and bottom edges are closed, so floating objects remain inside the screen
- Wild seeds, free bubbles, pollution zones, and a goal area
- Wild seeds release their neutral bubble when collected
- Safe walls block movement without hurting the player
- Spikes attached to walls burst the bubble on contact
- Win state, fail state, pause, and restart

## Adding a Level

Add or copy one dictionary in `levels/level_data.py`. Keep levels in play order and
provide the catalog fields `name`, `display_name`, `map_label`, `description`, and
`region` alongside the gameplay geometry.

The level-selection menu, region page, description panel, save display name, and
map-node layout are generated from those fields. Existing regions are `nursery`
and `thorn_reef`; adding a brand-new region still requires defining its display
name and progression rule.

## Project Structure

- `scenes/`: game-flow orchestration, input dispatch, and scene state
- `ui/`: rendering, layout, overlays, dialogs, and reusable widgets
- `core/`: save flow, level-state serialization, merge rules, audio, and game loop
- `entities/`: runtime game objects and their local physics
- `levels/`: ordered level definitions and catalog metadata

Dependencies flow from scenes into UI and core systems. UI and core modules do not
import scenes, which keeps rendering and game rules independently testable.
