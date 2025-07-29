# Star Trek Tactical Game

## Project Directory Structure

- `assets/` — Game assets such as images, fonts, and sounds.
- `data/` — Game constants and data definitions.
- `galaxy_generation/` — Code for procedural galaxy and map generation.
- `game_logic/` — Core game logic, rules, and state management.
- `ship/` — Ship classes, player/enemy ship logic, and ship systems.
- `tests/` — Unit and integration tests for game modules and UI.
- `ui/` — User interface components, rendering, and controls.
- `main.py` — Main entry point for running the game.
- `requirements.txt` — Python package dependencies.
- `README.md` — Project overview and documentation (this file).

---

Add further documentation below as the project evolves.

## Running the UI Wireframe

To run the UI wireframe demo, use the following command from the project root:

```sh
python -m ui.wireframe
```

**Note:** This ensures that Python can find all modules (like `galaxy_generation`) using the correct import paths. Running from inside the `ui/` folder or with `python ui/wireframe.py` may cause import errors.
