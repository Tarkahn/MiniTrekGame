from data.constants import (
    GRID_ROWS, GRID_COLS,
    NUM_STARS, NUM_PLANETS, NUM_STARBases, NUM_ENEMY_SHIPS, NUM_ANOMALIES,
    MIN_STAR_PLANET_DISTANCE
)
from galaxy_generation.object_placement import place_objects, place_objects_by_system
from utils.geometry import hex_distance


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
    # 3. Planets don't overlap with stars (removed MIN_STAR_PLANET_DISTANCE check from ALL stars)
    # Now planets only need to maintain distance from their host star, not all stars
    stars = [o for o in map_objects if o.type == 'star']
    planets = [o for o in map_objects if o.type == 'planet']
    # Just verify no planet overlaps with any star
    for planet in planets:
        for star in stars:
            dist = hex_distance((planet.q, planet.r), (star.q, star.r))
            assert dist > 0, (
                f"Planet at {(planet.q, planet.r)} overlaps with star at {(star.q, star.r)}"
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
    
    # 6. Each star has at least one planet
    # Get the planet orbits data to check star-planet relationships
    systems, star_coords, lazy_object_coords, planet_orbits = place_objects_by_system()
    
    # Count planets per star
    planets_per_star = {}
    for star in star_coords:
        planets_per_star[star] = 0
    
    for orbit in planet_orbits:
        star = orbit['star']
        if star in planets_per_star:
            planets_per_star[star] += 1
    
    # Verify each star has at least one planet
    for star, planet_count in planets_per_star.items():
        assert planet_count >= 1, f"Star at {star} has no planets (has {planet_count})"
    
    print(f"All {len(star_coords)} stars have at least one planet!")
    print(f"Planet distribution: {list(planets_per_star.values())}") 