import random
from collections import defaultdict
from data.constants import (
    GRID_ROWS, GRID_COLS,
    NUM_STARS, NUM_PLANETS, NUM_STARBases, NUM_ENEMY_SHIPS, NUM_ANOMALIES,
    MAX_STARS_PER_SYSTEM,
    MAX_PLANETS_PER_SYSTEM,
    MAX_STARBases_PER_SYSTEM
)
from .map_object import MapObject
import logging


def hex_distance(a, b):
    # a, b: (q, r) tuples
    dq = abs(a[0] - b[0])
    dr = abs(a[1] - b[1])
    ds = abs((-a[0] - a[1]) - (-b[0] - b[1]))
    return max(dq, dr, ds)


def all_hexes():
    # Returns all (q, r) pairs for the grid
    return [
        (q, r)
        for q in range(GRID_COLS)
        for r in range(GRID_ROWS)
    ]


def place_objects_by_system():
    occupied = set()
    systems = defaultdict(list)
    all_coords = set(all_hexes())
    all_objects = []

    # Place stars (eagerly, always present)
    star_coords = set()
    attempts = 0
    while len(star_coords) < NUM_STARS:
        if attempts > 1000:
            logging.warning(
                f"[PLACEMENT] Could only place {len(star_coords)} out of "
                f"{NUM_STARS} stars after 1000 attempts."
            )
            break
        candidate = random.choice(list(all_coords - occupied))
        star_coords.add(candidate)
        occupied.add(candidate)
        obj = MapObject('star', *candidate)
        systems[candidate].append(obj)
        all_objects.append(obj)
        attempts += 1
    logging.info(f"[PLACEMENT] Placed {len(star_coords)} stars.")

    # Only store star objects in systems at startup
    # All other objects will be generated lazily

    # For lazy loading, store the coordinates for each object type
    planet_coords = set()
    starbase_coords = set()
    enemy_coords = set()
    anomaly_coords = set()
    player_coord = None

    # Planets: Only place planets in systems with a star, up to MAX_PLANETS_PER_SYSTEM per star system
    total_planets_placed = 0
    star_list = list(star_coords)
    random.shuffle(star_list)
    for star in star_list:
        if total_planets_placed >= NUM_PLANETS:
            break
        num_planets = min(
            random.randint(0, MAX_PLANETS_PER_SYSTEM),
            NUM_PLANETS - total_planets_placed
        )
        # Place up to num_planets in this star system
        for _ in range(num_planets):
            planet_coords.add(star)
            total_planets_placed += 1
            if total_planets_placed >= NUM_PLANETS:
                break
    logging.info(
        f"[PLACEMENT] Placed {len(planet_coords)} planets."
    )

    # Starbases
    attempts = 0
    starbase_coords = set()
    starbase_placed = 0
    for _ in range(NUM_STARBases):
        if attempts > 1000:
            logging.warning(
                f"[PLACEMENT] Could only place {starbase_placed} out of "
                f"{NUM_STARBases} starbases after 1000 attempts."
            )
            break
        candidate = random.choice(list(all_coords - occupied))
        if candidate not in occupied:
            starbase_coords.add(candidate)
            occupied.add(candidate)
            starbase_placed += 1
        attempts += 1
    logging.info(f"[PLACEMENT] Placed {len(starbase_coords)} starbases.")

    # Enemies
    attempts = 0
    enemy_coords = set()
    enemy_placed = 0
    for _ in range(NUM_ENEMY_SHIPS):
        if attempts > 1000:
            logging.warning(
                f"[PLACEMENT] Could only place {enemy_placed} out of "
                f"{NUM_ENEMY_SHIPS} enemies after 1000 attempts."
            )
            break
        candidate = random.choice(list(all_coords - occupied))
        if candidate not in occupied:
            enemy_coords.add(candidate)
            occupied.add(candidate)
            enemy_placed += 1
        attempts += 1
    logging.info(f"[PLACEMENT] Placed {len(enemy_coords)} enemies.")

    # Anomalies
    attempts = 0
    anomaly_coords = set()
    anomaly_placed = 0
    for _ in range(NUM_ANOMALIES):
        if attempts > 1000:
            logging.warning(
                f"[PLACEMENT] Could only place {anomaly_placed} out of "
                f"{NUM_ANOMALIES} anomalies after 1000 attempts."
            )
            break
        candidate = random.choice(list(all_coords - occupied))
        if candidate not in occupied:
            anomaly_coords.add(candidate)
            occupied.add(candidate)
            anomaly_placed += 1
        attempts += 1
    logging.info(f"[PLACEMENT] Placed {len(anomaly_coords)} anomalies.")

    # Player
    attempts = 0
    player_coord = None
    while player_coord is None:
        if attempts > 1000:
            logging.warning("[PLACEMENT] Could not place player after 1000 attempts.")
            break
        candidate = random.choice(list(all_coords - occupied))
        if candidate not in occupied:
            player_coord = candidate
            occupied.add(candidate)
        attempts += 1
    if player_coord:
        logging.info(f"[PLACEMENT] Placed player at {player_coord}.")
    else:
        logging.warning("[PLACEMENT] Player not placed.")

    # Store the coordinates for lazy loading (only those actually placed)
    lazy_object_coords = {
        'planet': planet_coords,
        'starbase': starbase_coords,
        'enemy': enemy_coords,
        'anomaly': anomaly_coords,
        'player': {player_coord} if player_coord else set()
    }

    return systems, star_coords, lazy_object_coords


def generate_system_objects(q, r, lazy_object_coords, star_coords=None, grid_size=20):
    """Generate all objects for a given system hex (q, r), with random local positions and no overlaps."""
    objects_to_place = []
    # Add up to MAX_STARS_PER_SYSTEM if present in this system
    if star_coords and (q, r) in star_coords:
        star_count = min(
            sum(1 for coord in star_coords if coord == (q, r)),
            MAX_STARS_PER_SYSTEM
        )
        for _ in range(star_count):
            objects_to_place.append(('star', {}))
    # Add up to MAX_PLANETS_PER_SYSTEM planets if present
    if 'planet' in lazy_object_coords and (q, r) in lazy_object_coords['planet']:
        planet_count = min(
            sum(1 for coord in lazy_object_coords['planet'] if coord == (q, r)),
            MAX_PLANETS_PER_SYSTEM
        )
        for _ in range(planet_count):
            objects_to_place.append(('planet', {}))
    # Add up to MAX_STARBases_PER_SYSTEM starbases if present
    if 'starbase' in lazy_object_coords and (q, r) in lazy_object_coords['starbase']:
        starbase_count = min(
            sum(1 for coord in lazy_object_coords['starbase'] if coord == (q, r)),
            MAX_STARBases_PER_SYSTEM
        )
        for _ in range(starbase_count):
            objects_to_place.append(('starbase', {}))
    # Add all other objects (no per-system limit)
    for obj_type in ['enemy', 'anomaly', 'player']:
        if obj_type in lazy_object_coords and (q, r) in lazy_object_coords[obj_type]:
            count = sum(1 for coord in lazy_object_coords[obj_type] if coord == (q, r))
            for _ in range(count):
                objects_to_place.append((obj_type, {}))
    # Randomize unique positions for all objects
    max_attempts = 1000
    for attempt in range(max_attempts):
        used_positions = set()
        positions = []
        for _ in objects_to_place:
            while True:
                sys_q = random.randint(0, grid_size - 1)
                sys_r = random.randint(0, grid_size - 1)
                if (sys_q, sys_r) not in used_positions:
                    used_positions.add((sys_q, sys_r))
                    positions.append((sys_q, sys_r))
                    break
        if len(positions) == len(objects_to_place):
            break  # All unique
    # Build MapObject list
    result = []
    for (obj_type, props), (sys_q, sys_r) in zip(objects_to_place, positions):
        result.append(
            MapObject(
                obj_type,
                sys_q,
                sys_r,
                **props
            )
        )
    return result 