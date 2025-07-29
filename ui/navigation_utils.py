import math


def get_hex_neighbors(q, r):
    """Get all 6 neighboring hexes for a given hex coordinate."""
    # For flat-topped hexes with offset coordinates
    if q % 2 == 0:  # Even column
        neighbors = [
            (q-1, r-1), (q-1, r),    # Left neighbors
            (q, r-1), (q, r+1),      # Top and bottom
            (q+1, r-1), (q+1, r)     # Right neighbors
        ]
    else:  # Odd column
        neighbors = [
            (q-1, r), (q-1, r+1),    # Left neighbors
            (q, r-1), (q, r+1),      # Top and bottom
            (q+1, r), (q+1, r+1)     # Right neighbors
        ]
    return neighbors


def get_star_hexes(q, r):
    """Get all hexes occupied by a star (4 hexes total)."""
    # Star occupies center hex plus 3 adjacent hexes
    star_hexes = [(q, r)]  # Center
    neighbors = get_hex_neighbors(q, r)
    # Take first 3 neighbors for a compact cluster
    star_hexes.extend(neighbors[:3])
    return star_hexes


def get_planet_hexes(q, r):
    """Get all hexes occupied by a planet (2 hexes total)."""
    # Planet occupies center hex plus 1 adjacent hex
    planet_hexes = [(q, r)]  # Center
    neighbors = get_hex_neighbors(q, r)
    # Take first neighbor
    if neighbors:
        planet_hexes.append(neighbors[0])
    return planet_hexes


def is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid):
    """Check if a hex is blocked by a star or planet."""
    # Check stars
    for obj in systems.get(current_system, []):
        if obj.type == 'star' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
            star_hexes = get_star_hexes(obj.system_q, obj.system_r)
            if (q, r) in star_hexes:
                return True, 'star'
    
    # Check planets
    planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
    for orbit in planets_in_system:
        # Get star position to calculate planet position
        star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
        if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
            star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
            
            # Calculate current planet position from orbit
            planet_px = star_px + orbit['radius'] * math.cos(orbit['angle'])
            planet_py = star_py + orbit['radius'] * math.sin(orbit['angle'])
            
            # Convert to hex coordinates
            planet_q, planet_r = hex_grid.pixel_to_hex(planet_px, planet_py)
            
            # Check if the hex is occupied by this planet
            planet_hexes = get_planet_hexes(planet_q, planet_r)
            if (q, r) in planet_hexes:
                return True, 'planet'
    
    return False, None