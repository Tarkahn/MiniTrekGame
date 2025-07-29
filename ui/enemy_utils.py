"""
Enemy management utilities for the Star Trek Tactical Game
"""
import pygame
import random
import math
from ui.ui_config import *


def create_enemy_popup(enemy_id, enemy_obj, enemy_popups, font, small_font, title_font):
    """Create a popup window for enemy ship stats."""
    # Calculate popup window dimensions and position
    popup_width = 280
    popup_height = 350
    # Position popups in the dedicated dock area
    popup_dock_x = MAP_SIZE + RIGHT_EVENT_LOG_WIDTH  # Start of popup dock area
    popup_x = popup_dock_x + 10  # 10px padding from dock edge
    popup_y = STATUS_HEIGHT + 50 + (len(enemy_popups) * (popup_height + 10))  # Stack vertically below "Scan Results" label
    
    # Initialize enemy stats if not present
    if not hasattr(enemy_obj, 'health'):
        enemy_obj.health = 100
    if not hasattr(enemy_obj, 'max_health'):
        enemy_obj.max_health = 100
    if not hasattr(enemy_obj, 'energy'):
        enemy_obj.energy = 1000
    if not hasattr(enemy_obj, 'max_energy'):
        enemy_obj.max_energy = 1000
    if not hasattr(enemy_obj, 'shields'):
        enemy_obj.shields = 100  # Start with full shields
    if not hasattr(enemy_obj, 'max_shields'):
        enemy_obj.max_shields = 100
    if not hasattr(enemy_obj, 'ship_name'):
        enemy_obj.ship_name = f"Enemy Vessel {enemy_id}"
    if not hasattr(enemy_obj, 'ship_class'):
        ship_classes = ["Klingon Bird of Prey", "Romulan Warbird", "Gorn Destroyer", "Tholian Web Spinner"]
        enemy_obj.ship_class = random.choice(ship_classes)
    
    # Initialize power allocation system (0-9 scale) at full power
    if not hasattr(enemy_obj, 'power_allocation'):
        enemy_obj.power_allocation = {
            'phasers': 9,      # Full power
            'shields': 9,      
            'impulse': 9,
            'sensors': 9,
            'life_support': 9
        }
    
    # Initialize system integrity (0-100 scale) at full integrity
    if not hasattr(enemy_obj, 'system_integrity'):
        enemy_obj.system_integrity = {
            'hull': 100,
            'shields': 100,
            'phasers': 100,
            'impulse': 100,
            'sensors': 100,
            'life_support': 100,
            'warp_core': 100
        }
    
    # Create popup window info
    popup_info = {
        'window': None,  # Will be created when needed
        'surface': None,
        'rect': pygame.Rect(popup_x, popup_y, popup_width, popup_height),
        'font': font,  # Use loaded custom font
        'small_font': small_font,  # Use loaded custom small font
        'title_font': title_font,  # Use loaded custom title font
        'enemy_obj': enemy_obj,
        'enemy_id': enemy_id,
        'visible': False
    }
    
    return popup_info


def update_enemy_popups(enemy_popups, targeted_enemies, systems, current_system, add_event_log):
    """Update and clean up enemy popups for destroyed ships."""
    destroyed_enemies = []
    for enemy_id, popup_info in enemy_popups.items():
        enemy = popup_info['enemy_obj']
        # Check if enemy is destroyed
        if not hasattr(enemy, 'health') or enemy.health <= 0:
            destroyed_enemies.append(enemy_id)
        # Check if enemy is still in current system
        elif enemy not in systems.get(current_system, []):
            destroyed_enemies.append(enemy_id)
    
    # Remove destroyed enemies from tracking
    for enemy_id in destroyed_enemies:
        if enemy_id in enemy_popups:
            del enemy_popups[enemy_id]
        if enemy_id in targeted_enemies:
            del targeted_enemies[enemy_id]
            add_event_log(f"Target {enemy_id} lost - popup closed")


def get_enemy_id(enemy_obj, targeted_enemies, next_enemy_id):
    """Get or assign a unique ID to an enemy object."""
    # Check if this enemy already has an ID
    for enemy_id, tracked_enemy in targeted_enemies.items():
        if tracked_enemy is enemy_obj:
            return enemy_id
    
    # Assign new ID
    enemy_id = next_enemy_id
    return enemy_id


def perform_enemy_scan(enemy_obj, enemy_id, current_system, systems, enemy_scan_panel, add_event_log, sound_manager):
    """Perform a detailed scan of an enemy and add results to scan panel."""
    # Calculate distance from player
    player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
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
    
    # Generate realistic enemy data (simulate scan results)
    enemy_types = [
        "Klingon Bird of Prey",
        "Klingon Warship", 
        "Romulan Warbird",
        "Gorn Destroyer",
        "Orion Raider",
        "Tholian Vessel"
    ]
    
    # Use actual enemy object stats if available, otherwise generate defaults
    if hasattr(enemy_obj, 'ship_class'):
        enemy_name = enemy_obj.ship_class
    else:
        # Generate deterministic name based on position for consistency
        seed = enemy_obj.system_q * 1000 + enemy_obj.system_r
        random.seed(seed)
        enemy_name = random.choice(enemy_types)
        random.seed()  # Reset seed
    
    # Use actual enemy stats
    max_hull = getattr(enemy_obj, 'max_health', 100)
    current_hull = getattr(enemy_obj, 'health', max_hull)
    max_shields = getattr(enemy_obj, 'max_shields', 100) 
    current_shields = getattr(enemy_obj, 'shields', max_shields)
    max_energy = getattr(enemy_obj, 'max_energy', 1000)
    current_energy = getattr(enemy_obj, 'energy', max_energy)
    
    # Determine threat level based on stats and distance
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
    
    # Use actual enemy weapon status or generate standard loadout
    weapons = []
    weapons_status = getattr(enemy_obj, 'weapons_status', 'Online')
    if weapons_status == 'Online':
        # Standard enemy loadout when weapons are operational
        weapons.append("Disruptor Arrays")
        weapons.append("Photon Torpedoes")
    elif weapons_status == 'Damaged':
        weapons.append("Disruptor Arrays (Damaged)")
    # If offline, no weapons listed
    
    # Create scan data
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
        'system_integrity': getattr(enemy_obj, 'system_integrity', {}),
        'power_allocation': getattr(enemy_obj, 'power_allocation', {}),
        'weapons_status': getattr(enemy_obj, 'weapons_status', 'Unknown'),
        'engine_status': getattr(enemy_obj, 'engine_status', 'Unknown')
    }
    
    # Add to enemy scan panel
    enemy_scan_panel.add_scan_result(enemy_id, scan_data)
    
    # Log the scan
    add_event_log(f"Scanning {enemy_name} - Range: {distance:.1f}km, Threat: {threat_level}")
    
    # Play scan sound
    sound_manager.play_sound('scanner')