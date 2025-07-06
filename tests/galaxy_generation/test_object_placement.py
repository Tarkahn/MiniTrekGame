import pytest
from data.constants import (
    GRID_ROWS, GRID_COLS,
    NUM_STARS, NUM_PLANETS, NUM_STARBases, NUM_ENEMY_SHIPS, NUM_ANOMALIES,
    MIN_STAR_PLANET_DISTANCE
)
from galaxy_generation.object_placement import place_objects

def test_object_placement():
    map_objects, objects_by_type = place_objects()
    coords = set()
    # 1. No two objects occupy the same hex
    for obj in map_objects:
        pos = (obj.q, obj.r)
        assert pos not in coords, f"Overlap at {pos} for {obj.type}"
        coords.add(pos)
    # 2. All objects are within grid bounds
    for obj in map_objects:
        assert 0 <= obj.q < GRID_COLS, f"{obj.type} q out of bounds: {obj.q}"
        assert 0 <= obj.r < GRID_ROWS, f"{obj.type} r out of bounds: {obj.r}"
    # 3. Planets are at least MIN_STAR_PLANET_DISTANCE from all stars
    stars = [o for o in map_objects if o.type == 'star']
    planets = [o for o in map_objects if o.type == 'planet']
    def hex_distance(a, b):
        dq = abs(a[0] - b[0])
        dr = abs(a[1] - b[1])
        ds = abs((-a[0] - a[1]) - (-b[0] - b[1]))
        return max(dq, dr, ds)
    for planet in planets:
        for star in stars:
            dist = hex_distance((planet.q, planet.r), (star.q, star.r))
            assert dist >= MIN_STAR_PLANET_DISTANCE, (
                f"Planet at {(planet.q, planet.r)} too close to star at {(star.q, star.r)} (dist={dist})"
            )
    # 4. Correct number of each object type
    assert len(stars) == NUM_STARS, f"Expected {NUM_STARS} stars, got {len(stars)}"
    assert len(planets) == NUM_PLANETS, f"Expected {NUM_PLANETS} planets, got {len(planets)}"
    assert len(objects_by_type.get('starbase', [])) == NUM_STARBases
    assert len(objects_by_type.get('enemy', [])) == NUM_ENEMY_SHIPS
    assert len(objects_by_type.get('anomaly', [])) == NUM_ANOMALIES
    # 5. Player ship is present and unique
    players = objects_by_type.get('player', [])
    assert len(players) == 1, f"Expected 1 player ship, got {len(players)}" 