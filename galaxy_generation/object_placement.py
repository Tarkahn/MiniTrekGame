import random
from collections import defaultdict
from data.constants import (
    GRID_ROWS, GRID_COLS,
    NUM_STARS, NUM_PLANETS, NUM_STARBases, NUM_ENEMY_SHIPS, NUM_ANOMALIES,
    MAX_STARS_PER_SYSTEM,
    MAX_PLANETS_PER_SYSTEM,
    MAX_STARBases_PER_SYSTEM,
    MIN_STAR_PLANET_DISTANCE
)
from .map_object import MapObject
import logging
import math


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

    # Place stars with minimum separation
    star_coords = set()
    attempts = 0
    while len(star_coords) < NUM_STARS and attempts < 2000:
        if len(all_coords - occupied) == 0:
            logging.warning(
                f"[PLACEMENT] No more available coordinates. Placed {
                    len(star_coords)} out of "
                f"{NUM_STARS} stars."
            )
            break
        candidate = random.choice(list(all_coords - occupied))
        star_coords.add(candidate)
        occupied.add(candidate)
        obj = MapObject('star', *candidate)
        systems[candidate].append(obj)
        all_objects.append(obj)
        attempts += 1

    if attempts >= 2000:
        logging.warning(
            f"[PLACEMENT] Could only place {len(star_coords)} out of "
            f"{NUM_STARS} stars after 2000 attempts."
        )

    logging.info(f"[PLACEMENT] Placed {len(star_coords)} stars.")

    # Planets: Place up to NUM_PLANETS, distributing across all stars,
    # up to MAX_PLANETS_PER_SYSTEM per star
    planet_coords = set()
    planet_orbits = []  # List of dicts: {star, planet, radius, angle, speed}
    total_planets_placed = 0
    planets_per_star = {star: 0 for star in star_coords}
    # Track orbital distances per star to ensure proper spacing
    orbital_distances_per_star = {star: [] for star in star_coords}

    # Ensure we have stars to place planets around
    if not star_coords:
        logging.warning("[PLACEMENT] No stars available for planet placement.")
    else:
        star_list = list(star_coords)

        # PHASE 1: Ensure each star gets at least one planet
        logging.info(f"[PLACEMENT] Phase 1: Ensuring each star gets at least one planet...")
        stars_without_planets = star_list.copy()
        
        for star in stars_without_planets:
            if total_planets_placed >= NUM_PLANETS:
                break
                
            # Try to place a planet for this star
            placed = False
            for attempt in range(50):  # More attempts for the first planet
                # Generate orbital parameters
                orbit_angle = random.uniform(0, 2 * math.pi)
                
                # For the first planet of each star, choose from available distances
                existing_distances = orbital_distances_per_star[star]
                available_distances = []
                for dist in range(6, 16):  # 6 to 15 hexes
                    if dist not in existing_distances:
                        available_distances.append(dist)
                
                if not available_distances:
                    break  # No available distances for this star
                
                # Prefer closer distances for the first planet
                hex_dist = min(available_distances)
                
                # Calculate planet position
                dq = int(round(hex_dist * math.cos(orbit_angle)))
                dr = int(round(hex_dist * math.sin(orbit_angle)))
                planet_q = star[0] + dq
                planet_r = star[1] + dr
                planet_pos = (planet_q, planet_r)
                
                # Check if position is valid
                if (0 <= planet_q < GRID_COLS and 0 <= planet_r < GRID_ROWS and
                    planet_pos not in planet_coords and
                    planet_pos not in star_coords and
                    planet_pos not in occupied):
                    
                    actual_distance = hex_distance(planet_pos, star)
                    if 6 <= actual_distance <= 15:
                        # Check that the planet doesn't overlap with other stars (but can be closer than MIN_STAR_PLANET_DISTANCE)
                        # This allows planets to orbit their star even if other stars are nearby
                        overlaps_with_other_star = any(
                            hex_distance(planet_pos, other_star) == 0
                            for other_star in star_coords if other_star != star
                        )
                        
                        if not overlaps_with_other_star:
                            # Also check that the actual distance is unique for this star
                            if actual_distance not in orbital_distances_per_star[star]:
                                planet_coords.add(planet_pos)
                                occupied.add(planet_pos)
                                orbital_distances_per_star[star].append(actual_distance)
                                
                                # Create orbit data (speeds in radians per second)
                                # Base speed: closer planets orbit faster (inverse square law)
                                base_speed = 0.2 / (actual_distance * actual_distance)
                                speed_variation = random.uniform(0.7, 1.3)
                                orbit_speed = base_speed * speed_variation
                                # Clamp to reasonable bounds (radians per second)
                                orbit_speed = max(0.005, min(0.3, orbit_speed))
                                
                                planet_orbits.append({
                                    'star': star,
                                    'planet': planet_pos,
                                    'hex_radius': actual_distance,
                                    'angle': orbit_angle,
                                    'speed': orbit_speed
                                })
                                planets_per_star[star] += 1
                                total_planets_placed += 1
                                placed = True
                                break
            
            if not placed:
                logging.warning(f"[PLACEMENT] Could not place initial planet for star at {star}")
        
        # PHASE 2: Distribute remaining planets
        logging.info(f"[PLACEMENT] Phase 2: Distributing {NUM_PLANETS - total_planets_placed} remaining planets...")
        max_total_attempts = (NUM_PLANETS - total_planets_placed) * 10
        total_attempts = 0

        while total_planets_placed < NUM_PLANETS and star_list and total_attempts < max_total_attempts:
            # Pick a random star that hasn't reached its planet limit
            available_stars = [
                s for s in star_list if planets_per_star[s] < MAX_PLANETS_PER_SYSTEM]
            if not available_stars:
                logging.warning(f"[PLACEMENT] All stars have reached maximum planet capacity. Placed {
                                total_planets_placed} planets.")
                break

            star = random.choice(available_stars)

            # Try to find a valid planet position for this star
            placed_for_star = False
            for attempt in range(20):  # Try 20 times per star
                # Generate orbital parameters with proper spacing
                orbit_angle = random.uniform(0, 2 * math.pi)
                
                # Calculate a unique orbital distance for this star
                existing_distances = orbital_distances_per_star[star]
                
                # Try to find a unique orbital distance
                available_distances = []
                for dist in range(6, 16):  # 6 to 15 hexes
                    if dist not in existing_distances:
                        available_distances.append(dist)
                
                if not available_distances:
                    continue  # No available unique distances for this star
                
                # Choose a random available distance
                hex_dist = random.choice(available_distances)

                # Calculate planet position using proper hex coordinate math
                # For hex grids, we need to convert the polar coordinates properly
                dq = int(round(hex_dist * math.cos(orbit_angle)))
                dr = int(round(hex_dist * math.sin(orbit_angle)))

                planet_q = star[0] + dq
                planet_r = star[1] + dr
                planet_pos = (planet_q, planet_r)

                # Check if position is valid
                if (0 <= planet_q < GRID_COLS and 0 <= planet_r < GRID_ROWS and
                    planet_pos not in planet_coords and
                    planet_pos not in star_coords and
                        planet_pos not in occupied):

                    # Verify the planet is actually within the desired orbital distance from its host star
                    actual_distance = hex_distance(planet_pos, star)
                    # Respect minimum distance requirement (5 hexes minimum, max 15)
                    if 6 <= actual_distance <= 15:

                        # Check that the planet doesn't overlap with other stars (but can be closer than MIN_STAR_PLANET_DISTANCE)
                        # This allows planets to orbit their star even if other stars are nearby
                        overlaps_with_other_star = any(
                            hex_distance(planet_pos, other_star) == 0
                            for other_star in star_coords if other_star != star
                        )

                        # Simplified: only check no overlap with other stars
                        if not overlaps_with_other_star:
                            # Also check that the actual distance is unique for this star
                            if actual_distance not in orbital_distances_per_star[star]:
                                planet_coords.add(planet_pos)
                                occupied.add(planet_pos)  # Mark as occupied

                                # Track this orbital distance
                                orbital_distances_per_star[star].append(actual_distance)

                                # Create orbit data (speeds in radians per second)
                                # Make orbital speed inversely related to distance (farther = slower, more realistic)
                                # Inverse square relationship
                                base_speed = 0.2 / (actual_distance * actual_distance)
                                speed_variation = random.uniform(0.7, 1.3)  # ±30% variation
                                orbit_speed = base_speed * speed_variation
                                # Clamp to reasonable bounds (radians per second)
                                orbit_speed = max(0.005, min(0.3, orbit_speed))
                                planet_orbits.append({
                                    'star': star,
                                    'planet': planet_pos,
                                    'hex_radius': actual_distance,
                                    'angle': orbit_angle,
                                    'speed': orbit_speed
                                })
                                planets_per_star[star] += 1
                                total_planets_placed += 1
                                placed_for_star = True
                                break

                total_attempts += 1

            if not placed_for_star:
                logging.debug(f"[PLACEMENT] Could not place planet around star {
                              star} after 20 attempts.")

        if total_attempts >= max_total_attempts:
            logging.warning(f"[PLACEMENT] Reached maximum placement attempts. Placed {
                            total_planets_placed} of {NUM_PLANETS} planets.")

    logging.info(f"[PLACEMENT] Placed {len(planet_coords)} planets with {
                 len(planet_orbits)} orbits.")
    
    # Log stars without planets
    stars_without_planets = [star for star in star_coords if planets_per_star[star] == 0]
    if stars_without_planets:
        logging.warning(f"[PLACEMENT] {len(stars_without_planets)} stars have no planets: {stars_without_planets}")
    else:
        logging.info("[PLACEMENT] All stars have at least one planet.")

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

    # Anomalies (moved up before enemies)
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

    # Enemies - Place in pairs within systems
    attempts = 0
    enemy_coords = []  # Changed to list to allow duplicates for pairs
    enemy_coords_set = set()  # Track unique systems with enemies
    enemy_placed = 0
    player_coord = None  # Initialize player_coord before using it
    # For enemy placement, only consider as occupied: enemies, starbases, anomalies, player
    enemy_blocked = set()
    enemy_blocked.update(starbase_coords)
    enemy_blocked.update(anomaly_coords)
    if player_coord:
        enemy_blocked.add(player_coord)
    
    # Place enemies in pairs - we need NUM_ENEMY_SHIPS total, so NUM_ENEMY_SHIPS/2 systems with pairs
    enemy_systems_needed = NUM_ENEMY_SHIPS // 2
    if NUM_ENEMY_SHIPS % 2 == 1:
        enemy_systems_needed += 1  # If odd number, we'll have one system with a single enemy
    
    # Get list of available coordinates that aren't blocked
    available_coords = list(all_coords - enemy_blocked)
    random.shuffle(available_coords)
    
    # Select systems for enemy pairs
    enemy_systems = []
    for i in range(min(enemy_systems_needed, len(available_coords))):
        if enemy_placed >= NUM_ENEMY_SHIPS:
            break
        system_coord = available_coords[i]
        enemy_systems.append(system_coord)
        enemy_coords_set.add(system_coord)
        
        # Place first enemy in this system
        enemy_coords.append(system_coord)
        enemy_placed += 1
        
        # Place second enemy in same system (if we haven't reached the limit)
        if enemy_placed < NUM_ENEMY_SHIPS:
            # For the second enemy, we use the same system coordinate
            # The actual positions within the system will be randomized when the system is generated
            enemy_coords.append(system_coord)
            enemy_placed += 1
    
    logging.info(
        f"[PLACEMENT] Placed {enemy_placed} enemies across {len(enemy_systems)} systems (in pairs)."
    )

    # Player
    attempts = 0
    player_coord = None
    while player_coord is None:
        if attempts > 1000:
            logging.warning(
                "[PLACEMENT] Could not place player after 1000 attempts.")
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
    # Note: planets are handled separately in planet_orbits, not in lazy_object_coords
    # Enemy coords is now a list to support multiple enemies per system
    lazy_object_coords = {
        'starbase': starbase_coords,
        'enemy': enemy_coords,  # This is now a list with duplicates for pairs
        'anomaly': anomaly_coords,
        'player': {player_coord} if player_coord else set()
    }

    return systems, star_coords, lazy_object_coords, planet_orbits


def generate_system_objects(q, r, lazy_object_coords, star_coords=None, planet_orbits=None, grid_size=20):
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
    # Planets are now stored in planet_orbits, not lazy_object_coords
    if planet_orbits:
        planets_in_system = [
            orbit for orbit in planet_orbits if orbit['star'] == (q, r)]
        planet_count = min(len(planets_in_system), MAX_PLANETS_PER_SYSTEM)
        for _ in range(planet_count):
            objects_to_place.append(('planet', {}))
    # Add up to MAX_STARBases_PER_SYSTEM starbases if present
    if 'starbase' in lazy_object_coords and (q, r) in lazy_object_coords['starbase']:
        starbase_count = min(
            sum(1 for coord in lazy_object_coords['starbase'] if coord == (
                q, r)),
            MAX_STARBases_PER_SYSTEM
        )
        for _ in range(starbase_count):
            objects_to_place.append(('starbase', {}))
    # Add all other objects (no per-system limit)
    for obj_type in ['enemy', 'anomaly', 'player']:
        if obj_type in lazy_object_coords:
            if obj_type == 'enemy':
                # Enemy coords is a list, count occurrences
                count = lazy_object_coords[obj_type].count((q, r))
            else:
                # Other types are sets
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


def place_objects():
    """
    Backward compatibility wrapper for place_objects_by_system.
    Returns (map_objects, objects_by_type) as expected by tests.
    """
    systems, star_coords, lazy_object_coords, planet_orbits = place_objects_by_system()

    # Create list of all map objects
    map_objects = []
    objects_by_type = {}

    # Add stars
    for star_coord in star_coords:
        star_obj = MapObject('star', star_coord[0], star_coord[1])
        map_objects.append(star_obj)
        objects_by_type.setdefault('star', []).append(star_obj)

    # Add planets from orbits (this is the authoritative source)
    for orbit in planet_orbits:
        planet_coord = orbit['planet']
        planet_obj = MapObject('planet', planet_coord[0], planet_coord[1])
        map_objects.append(planet_obj)
        objects_by_type.setdefault('planet', []).append(planet_obj)

    # Add other objects (excluding planets since they're in orbits)
    for obj_type, coords_data in lazy_object_coords.items():
        if obj_type in ['planet', 'player']:
            continue  # Skip planets (handled above) and player (handled below)
        
        # Handle enemy coords as list, others as sets
        if obj_type == 'enemy':
            # Enemy coords is a list with potential duplicates
            for coord in coords_data:
                obj = MapObject(obj_type, coord[0], coord[1])
                map_objects.append(obj)
                objects_by_type.setdefault(obj_type, []).append(obj)
        else:
            # Other types are sets
            for coord in coords_data:
                obj = MapObject(obj_type, coord[0], coord[1])
                map_objects.append(obj)
                objects_by_type.setdefault(obj_type, []).append(obj)

    # Add player
    player_coords = lazy_object_coords.get('player', set())
    if player_coords:
        player_coord = next(iter(player_coords))
        player_obj = MapObject('player', player_coord[0], player_coord[1])
        map_objects.append(player_obj)
        objects_by_type.setdefault('player', []).append(player_obj)

    return map_objects, objects_by_type
