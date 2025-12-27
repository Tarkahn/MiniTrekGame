"""
Hex grid utilities for the Star Trek Tactical Game
"""
from utils.geometry import hex_distance, hex_neighbors

# Re-export hex_distance for convenience
__all__ = ['hex_distance', 'get_hex_neighbors', 'get_star_hexes', 'get_planet_hexes', 'is_hex_blocked']


def get_hex_neighbors(q, r):
    """Get all 6 neighboring hexes for a given hex coordinate.

    This is a wrapper around utils.geometry.hex_neighbors for backwards compatibility.
    """
    return hex_neighbors(q, r)


def get_star_hexes(q, r):
    """Get all hexes occupied by a star (4 hexes total)."""
    # Star occupies center hex plus 3 adjacent hexes
    hexes = [(q, r)]  # Center hex
    neighbors = get_hex_neighbors(q, r)
    # Choose 3 adjacent hexes (forming a cluster)
    if len(neighbors) >= 3:
        hexes.extend(neighbors[:3])
    return hexes


def get_planet_hexes(q, r):
    """Get all hexes occupied by a planet (1-4 hexes based on size)."""
    # For now, just return the single hex
    # Could expand to variable sizes later
    return [(q, r)]


def is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid):
    """Check if a hex is blocked by objects or multi-hex entities."""
    # Check if hex is out of bounds
    if q < 0 or q >= hex_grid.cols or r < 0 or r >= hex_grid.rows:
        return True, 'boundary'
    
    # Check objects in current system
    for obj in systems.get(current_system, []):
        # Check if this hex is part of a star
        if obj.type == 'star':
            star_hexes = get_star_hexes(obj.q, obj.r)
            if (q, r) in star_hexes:
                return True, 'star'
        # Check if hex contains any other object type
        elif obj.q == q and obj.r == r and obj.type != 'player':
            return True, obj.type
    
    # Check if hex contains a planet (from orbits)
    for orbit in planet_orbits:
        if orbit['star'] == current_system:
            planet_pos = orbit['planet']
            planet_hexes = get_planet_hexes(planet_pos[0], planet_pos[1])
            if (q, r) in planet_hexes:
                return True, 'planet'
            
    return False, None