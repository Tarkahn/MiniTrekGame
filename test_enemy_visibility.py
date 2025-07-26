"""
Test script to verify enemy placement in star+planet systems
Run this before starting the game to see which systems should have enemies
"""

import sys
sys.path.append('.')
from galaxy_generation.object_placement import place_objects_by_system, generate_system_objects
from data.constants import *
import random

print("=== ENEMY PLACEMENT TEST ===\n")
print("This script will show you which star+planet systems have enemies.")
print("Write down a few coordinates and visit them in the game to verify.\n")

# Use the same seed as the game will use
random.seed()  # No fixed seed - same as game

systems, star_coords, lazy_object_coords, planet_orbits = place_objects_by_system()

enemy_coords = lazy_object_coords.get('enemy', [])
star_systems = set(star_coords)
systems_with_planets = set(orbit['star'] for orbit in planet_orbits)

# Find star+planet systems with enemies
star_planet_with_enemies = []
for coord in star_systems:
    if coord in systems_with_planets:
        enemy_count = enemy_coords.count(coord)
        if enemy_count > 0:
            star_planet_with_enemies.append((coord, enemy_count))

print(f"Found {len(star_planet_with_enemies)} star+planet systems with enemies:\n")

# Show first 10
for i, (coord, count) in enumerate(star_planet_with_enemies[:10]):
    print(f"{i+1}. System at {coord}: {count} enemies")
    
    # Generate the system to verify
    objs = generate_system_objects(
        coord[0], coord[1], 
        lazy_object_coords, 
        star_coords=star_coords, 
        planet_orbits=planet_orbits
    )
    
    # Count actual enemies
    actual_enemies = sum(1 for obj in objs if obj.type == 'enemy')
    if actual_enemies != count:
        print(f"   WARNING: Generated {actual_enemies} enemies instead of {count}!")

print(f"\nNOTE: Visit these systems in the game. The event log should show:")
print("  [SYSTEM TYPE] STAR+PLANET")
print("  [DEBUG] Expected enemies from placement: X")
print("  [ENEMIES] X enemy ships detected")
print("\nIf you see '[ENEMIES] No enemy ships in this system' for these coordinates,")
print("then there's a bug in the game's system generation.")