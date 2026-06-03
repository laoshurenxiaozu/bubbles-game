# Bubbles

A small Pygame prototype for an adventure puzzle game about carrying a life seed inside a bubble.

## Run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

## Controls

- `A` / `D` or left / right arrows: move horizontally
- `W`: release one collected seed downward
- `S`: split off one bubble upward
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
