"""
Scanning functions for planets, stars, and enemy ships.

This module handles detailed scanning operations that reveal information
about celestial objects and enemy vessels in the game.
"""

import os
import math
import random
import pygame
from data.constants import (PLANET_CLASSES, STAR_CLASSES, ANOMALY_CLASSES,
                            ENEMY_HULL_STRENGTH, ENEMY_SHIELD_CAPACITY)


def perform_planet_scan(planet_q, planet_r, current_system, add_event_log, sound_manager):
    """Perform a detailed scan of a planet and return results.

    Args:
        planet_q: Planet hex Q coordinate
        planet_r: Planet hex R coordinate
        current_system: Current system coordinates tuple
        add_event_log: Function to add messages to event log
        sound_manager: Sound manager instance

    Returns:
        Tuple of (scan_data dict, planet_image or None)
    """
    planet_classes = list(PLANET_CLASSES.keys())
    position_seed = f"{planet_q}_{planet_r}_{current_system}"
    planet_type = planet_classes[hash(position_seed) % len(planet_classes)]

    planet_info = PLANET_CLASSES[planet_type]

    # Select random image for this planet type
    available_images = planet_info['images']
    image_filename = available_images[hash(position_seed + "_image") % len(available_images)]

    # Load the planet image
    planet_image = None
    try:
        image_path = os.path.join('assets', 'planets', image_filename)
        planet_image = pygame.image.load(image_path)
    except pygame.error as e:
        print(f"Failed to load planet image {image_filename}: {e}")

    # Create scan data
    scan_data = {
        'type': 'planet',
        'class': planet_type,
        'name': planet_info['name'],
        'description': planet_info['description'],
        'position': (planet_q, planet_r),
        'image': image_filename
    }

    # Log the scan
    add_event_log(f"Scanning {planet_info['name']} at ({planet_q}, {planet_r})")
    add_event_log(f"Class {planet_type}: {planet_info['description']}")

    # Play scan sound
    sound_manager.play_sound('scanner')

    return scan_data, planet_image


def perform_star_scan(star_q, star_r, current_system, add_event_log, sound_manager):
    """Perform a detailed scan of a star and return results.

    Args:
        star_q: Star hex Q coordinate
        star_r: Star hex R coordinate
        current_system: Current system coordinates tuple
        add_event_log: Function to add messages to event log
        sound_manager: Sound manager instance

    Returns:
        Tuple of (scan_data dict, star_image or None)
    """
    star_classes = list(STAR_CLASSES.keys())
    position_seed = f"{star_q}_{star_r}_{current_system}"
    star_type = star_classes[hash(position_seed) % len(star_classes)]

    star_info = STAR_CLASSES[star_type]

    # Select image for this star type
    available_images = star_info['images']
    image_filename = available_images[hash(position_seed + "_image") % len(available_images)]

    # Load the star image
    star_image = None
    try:
        image_path = os.path.join('assets', 'stars', image_filename)
        star_image = pygame.image.load(image_path)
    except pygame.error as e:
        print(f"Failed to load star image {image_filename}: {e}")

    # Create scan data
    scan_data = {
        'type': 'star',
        'class': star_type,
        'name': star_info['name'],
        'description': star_info['description'],
        'position': (star_q, star_r),
        'image': image_filename
    }

    # Log the scan
    add_event_log(f"Scanning {star_info['name']} at ({star_q}, {star_r})")
    add_event_log(f"{star_type.replace('_', ' ').title()}: {star_info['description']}")

    # Play scan sound
    sound_manager.play_sound('scanner')

    return scan_data, star_image


def perform_anomaly_scan(anomaly_obj, current_system, add_event_log, sound_manager):
    """Perform a detailed scan of an anomaly and return results.

    Args:
        anomaly_obj: The anomaly MapObject to scan
        current_system: Current system coordinates tuple
        add_event_log: Function to add messages to event log
        sound_manager: Sound manager instance

    Returns:
        Tuple of (scan_data dict, anomaly_image or None)
    """
    # Get anomaly type from the object's props
    anomaly_type = anomaly_obj.props.get('anomaly_type', None)

    # If no type stored, pick one randomly based on position for consistency
    if not anomaly_type:
        position_seed = f"{anomaly_obj.system_q}_{anomaly_obj.system_r}_{current_system}"
        anomaly_types = list(ANOMALY_CLASSES.keys())
        anomaly_type = anomaly_types[hash(position_seed) % len(anomaly_types)]

    # Get anomaly info from constants
    anomaly_info = ANOMALY_CLASSES.get(anomaly_type, {
        'name': 'Unknown Anomaly',
        'description': 'Unidentified spatial phenomenon. Recommend caution.',
        'danger_level': 'UNKNOWN',
        'images': []
    })

    # Select image for this anomaly
    available_images = anomaly_info.get('images', [])
    image_filename = None
    if available_images:
        position_seed = f"{anomaly_obj.system_q}_{anomaly_obj.system_r}_{current_system}_image"
        image_filename = available_images[hash(position_seed) % len(available_images)]

    # Load the anomaly image
    anomaly_image = None
    if image_filename:
        try:
            image_path = os.path.join('assets', 'anomalies', image_filename)
            anomaly_image = pygame.image.load(image_path)
        except pygame.error as e:
            print(f"Failed to load anomaly image {image_filename}: {e}")

    # Create scan data
    scan_data = {
        'type': 'anomaly',
        'anomaly_type': anomaly_type,
        'name': anomaly_info['name'],
        'description': anomaly_info['description'],
        'danger_level': anomaly_info.get('danger_level', 'UNKNOWN'),
        'position': (anomaly_obj.system_q, anomaly_obj.system_r),
        'image': image_filename
    }

    # Log the scan with danger level color coding
    danger_level = anomaly_info.get('danger_level', 'UNKNOWN')
    add_event_log(f"*** ANOMALY DETECTED ***")
    add_event_log(f"Scanning {anomaly_info['name']} at ({anomaly_obj.system_q}, {anomaly_obj.system_r})")
    add_event_log(f"Danger Level: {danger_level}")
    add_event_log(f"{anomaly_info['description']}")

    # Play scan sound
    sound_manager.play_sound('scanner')

    return scan_data, anomaly_image


def perform_enemy_scan(enemy_obj, enemy_id, systems, game_state, enemy_scan_panel,
                       add_event_log, sound_manager, player_ship=None):
    """Perform a detailed scan of an enemy and add results to scan panel.

    Args:
        enemy_obj: The enemy MapObject to scan
        enemy_id: Unique identifier for the enemy
        systems: Dictionary of system objects
        game_state: Current game state
        enemy_scan_panel: Panel to display scan results
        add_event_log: Function to add messages to event log
        sound_manager: Sound manager instance
        player_ship: PlayerShip instance for accessing combat manager
    """
    # Calculate distance from player
    player_obj = next((obj for obj in systems.get(game_state.current_system, [])
                       if obj.type == 'player'), None)
    if player_obj and hasattr(player_obj, 'system_q') and hasattr(player_obj, 'system_r'):
        dx = enemy_obj.system_q - player_obj.system_q
        dy = enemy_obj.system_r - player_obj.system_r
        distance = math.sqrt(dx * dx + dy * dy)

        # Calculate bearing (0-360 degrees)
        bearing = math.degrees(math.atan2(dy, dx))
        if bearing < 0:
            bearing += 360
    else:
        distance = 0
        bearing = 0

    # Get faction from enemy object
    enemy_faction = getattr(enemy_obj, 'faction', None) or 'klingon'

    # Get the actual EnemyShip instance from the combat manager
    enemy_ship = None
    if player_ship and hasattr(player_ship, 'combat_manager'):
        enemy_ship = player_ship.combat_manager.get_or_create_enemy_ship(enemy_obj, player_ship)

    # Get actual values from the EnemyShip if available
    if enemy_ship:
        enemy_name = enemy_ship.name
        max_hull = enemy_ship.max_hull_strength
        max_shields = enemy_ship.max_shields
        max_energy = enemy_ship.max_warp_core_energy
        current_hull = enemy_ship.hull_strength
        current_shields = enemy_ship.shields  # Uses property that reads from shield_system
        current_energy = enemy_ship.warp_core_energy
        system_integrity = enemy_ship.system_integrity.copy()
        power_allocation = enemy_ship.power_allocation.copy()
        enemy_faction = enemy_ship.faction  # Get faction from ship if available
    else:
        # Fallback to legacy random generation if no EnemyShip exists
        # Use faction-appropriate ship types
        if enemy_faction == 'romulan':
            enemy_types = [
                "Romulan Warbird",
                "Romulan Scout",
                "Romulan D'deridex",
                "Romulan Valdore"
            ]
        else:
            enemy_types = [
                "Klingon Bird of Prey",
                "Klingon Warship",
                "Klingon D7 Cruiser",
                "Klingon Vor'cha"
            ]
        seed = enemy_obj.system_q * 1000 + enemy_obj.system_r
        random.seed(seed)
        enemy_name = random.choice(enemy_types)
        max_hull = ENEMY_HULL_STRENGTH
        max_shields = ENEMY_SHIELD_CAPACITY
        max_energy = 1000
        current_hull = random.randint(int(max_hull * 0.85), max_hull)
        current_shields = random.randint(int(max_shields * 0.8), max_shields)
        current_energy = random.randint(int(max_energy * 0.8), max_energy)
        system_integrity = {
            'hull': current_hull, 'shields': 100, 'phasers': 100,
            'engines': 100, 'warp_core': 100
        }
        power_allocation = {'phasers': 5, 'shields': 5, 'engines': 5}
        random.seed()

    # Determine threat level
    hull_ratio = current_hull / max_hull
    shield_ratio = current_shields / max_shields if max_shields > 0 else 0
    energy_ratio = current_energy / max_energy

    overall_strength = (hull_ratio + shield_ratio + energy_ratio) / 3

    if distance < 2 and overall_strength > 0.7:
        threat_level = "Critical"
    elif distance < 4 and overall_strength > 0.5:
        threat_level = "High"
    elif overall_strength > 0.3:
        threat_level = "Medium"
    else:
        threat_level = "Low"

    # Generate weapon list (deterministic based on position if no enemy_ship)
    weapons = ["Disruptor Arrays", "Photon Torpedoes"]  # All Klingon ships have these

    # Create scan data with actual system integrity and power allocation
    scan_data = {
        'name': enemy_name,
        'position': (enemy_obj.system_q, enemy_obj.system_r),
        'hull': current_hull,
        'max_hull': max_hull,
        'shields': current_shields,
        'max_shields': max_shields,
        'energy': current_energy,
        'max_energy': max_energy,
        'weapons': weapons,
        'distance': distance,
        'bearing': bearing,
        'threat_level': threat_level,
        'system_integrity': system_integrity,
        'power_allocation': power_allocation
    }

    # Add to enemy scan panel
    enemy_scan_panel.add_scan_result(enemy_id, scan_data)

    # Log the scan
    add_event_log(f"Scanning {enemy_name} - Range: {distance:.1f}km, Threat: {threat_level}")

    # Play scan sound
    sound_manager.play_sound('scanner')


def get_enemy_current_position(enemy_obj, hex_grid, player_ship):
    """Get the current position of an enemy (animated if moving, otherwise static).

    Args:
        enemy_obj: The enemy MapObject
        hex_grid: The hex grid for coordinate conversion
        player_ship: Player ship instance (for combat manager access)

    Returns:
        Tuple of (x, y) pixel coordinates
    """
    enemy_ship_id = id(enemy_obj)

    if hasattr(player_ship, 'combat_manager') and enemy_ship_id in player_ship.combat_manager.enemy_ships:
        enemy_ship = player_ship.combat_manager.enemy_ships[enemy_ship_id]
        dynamic_position = enemy_ship.get_render_position()
        return hex_grid.get_hex_center(dynamic_position[0], dynamic_position[1])

    # Fallback to legacy animation positions
    if hasattr(enemy_obj, 'anim_px') and hasattr(enemy_obj, 'anim_py'):
        return (enemy_obj.anim_px, enemy_obj.anim_py)
    elif hasattr(enemy_obj, 'system_q') and hasattr(enemy_obj, 'system_r'):
        return hex_grid.get_hex_center(enemy_obj.system_q, enemy_obj.system_r)
    else:
        return hex_grid.get_hex_center(0, 0)


def update_enemy_scan_positions(enemy_scan_panel, systems, game_state, player_ship,
                                get_enemy_id_func):
    """Update scan panel positions for all scanned enemies that are moving.

    Args:
        enemy_scan_panel: Panel displaying enemy scan results
        systems: Dictionary of system objects
        game_state: Current game state
        player_ship: Player ship instance
        get_enemy_id_func: Function to get enemy ID from enemy object
    """
    for enemy_id, scan_data in enemy_scan_panel.scanned_enemies.items():
        # Find the actual enemy object by ID in current system
        for obj in systems.get(game_state.current_system, []):
            if obj.type == 'enemy' and get_enemy_id_func(obj) == enemy_id:
                enemy_ship_id = id(obj)
                if enemy_ship_id in player_ship.combat_manager.enemy_ships:
                    enemy_ship = player_ship.combat_manager.enemy_ships[enemy_ship_id]
                    current_hex_pos = enemy_ship.position

                    if current_hex_pos != scan_data['position']:
                        scan_data['position'] = current_hex_pos

                        # Recalculate distance and bearing from player
                        player_obj = next((o for o in systems.get(game_state.current_system, [])
                                           if o.type == 'player'), None)
                        if player_obj and hasattr(player_obj, 'system_q') and hasattr(player_obj, 'system_r'):
                            dx = current_hex_pos[0] - player_obj.system_q
                            dy = current_hex_pos[1] - player_obj.system_r
                            scan_data['distance'] = math.sqrt(dx * dx + dy * dy)
                            bearing = math.degrees(math.atan2(dy, dx))
                            if bearing < 0:
                                bearing += 360
                            scan_data['bearing'] = bearing
                break


def update_enemy_scan_stats(enemy_scan_panel, systems, game_state, player_ship,
                            get_enemy_id_func):
    """Update scan panel stats for all scanned enemies (hull, shields, energy, etc.).

    This should be called each frame to keep the scan panel up to date with
    the actual enemy ship state after damage.

    Args:
        enemy_scan_panel: Panel displaying enemy scan results
        systems: Dictionary of system objects
        game_state: Current game state
        player_ship: Player ship instance
        get_enemy_id_func: Function to get enemy ID from enemy object
    """
    if not hasattr(player_ship, 'combat_manager'):
        return

    for enemy_id, scan_data in enemy_scan_panel.scanned_enemies.items():
        # Find the actual enemy object by ID in current system
        for obj in systems.get(game_state.current_system, []):
            if obj.type == 'enemy' and get_enemy_id_func(obj) == enemy_id:
                enemy_ship_id = id(obj)
                if enemy_ship_id in player_ship.combat_manager.enemy_ships:
                    enemy_ship = player_ship.combat_manager.enemy_ships[enemy_ship_id]

                    # Update all stats from the actual EnemyShip
                    scan_data['hull'] = enemy_ship.hull_strength
                    scan_data['max_hull'] = enemy_ship.max_hull_strength
                    scan_data['shields'] = enemy_ship.shields  # Property reads from shield_system
                    scan_data['max_shields'] = enemy_ship.max_shields
                    scan_data['energy'] = enemy_ship.warp_core_energy
                    scan_data['max_energy'] = enemy_ship.max_warp_core_energy
                    scan_data['system_integrity'] = enemy_ship.system_integrity.copy()
                    scan_data['power_allocation'] = enemy_ship.power_allocation.copy()

                    # Update threat level based on current state
                    hull_ratio = scan_data['hull'] / scan_data['max_hull'] if scan_data['max_hull'] > 0 else 0
                    shield_ratio = scan_data['shields'] / scan_data['max_shields'] if scan_data['max_shields'] > 0 else 0
                    energy_ratio = scan_data['energy'] / scan_data['max_energy'] if scan_data['max_energy'] > 0 else 0
                    overall_strength = (hull_ratio + shield_ratio + energy_ratio) / 3
                    distance = scan_data.get('distance', 0)

                    if distance < 2 and overall_strength > 0.7:
                        scan_data['threat_level'] = "Critical"
                    elif distance < 4 and overall_strength > 0.5:
                        scan_data['threat_level'] = "High"
                    elif overall_strength > 0.3:
                        scan_data['threat_level'] = "Medium"
                    else:
                        scan_data['threat_level'] = "Low"
                break
