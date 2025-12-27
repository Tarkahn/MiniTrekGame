"""
Enemy popup management for displaying enemy ship stats.

This module handles the creation, drawing, and updating of enemy ship
popup windows in the game UI.
"""

import pygame
import random
from data.constants import ENEMY_SHIELD_CAPACITY


def create_enemy_popup(enemy_id, enemy_obj, game_state, map_size, right_event_log_width,
                       status_height, font, small_font, title_font):
    """Create a popup window for enemy ship stats.

    Args:
        enemy_id: Unique identifier for the enemy
        enemy_obj: The enemy MapObject
        game_state: Current game state
        map_size: Size of the map in pixels
        right_event_log_width: Width of the event log panel
        status_height: Height of the status bar
        font: Main font for text
        small_font: Small font for details
        title_font: Title font for headers

    Returns:
        Dictionary containing popup configuration and state
    """
    popup_width = 280
    popup_height = 350
    popup_dock_x = map_size + right_event_log_width
    popup_x = popup_dock_x + 10
    popup_y = status_height + 50 + (len(game_state.scan.enemy_popups) * (popup_height + 10))

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
        enemy_obj.shields = ENEMY_SHIELD_CAPACITY
    if not hasattr(enemy_obj, 'max_shields'):
        enemy_obj.max_shields = ENEMY_SHIELD_CAPACITY
    if not hasattr(enemy_obj, 'ship_name'):
        enemy_obj.ship_name = f"Enemy Vessel {enemy_id}"
    if not hasattr(enemy_obj, 'ship_class'):
        ship_classes = ["Klingon Bird of Prey", "Romulan Warbird", "Gorn Destroyer", "Tholian Web Spinner"]
        enemy_obj.ship_class = random.choice(ship_classes)

    popup_info = {
        'window': None,
        'surface': None,
        'rect': pygame.Rect(popup_x, popup_y, popup_width, popup_height),
        'font': font,
        'small_font': small_font,
        'title_font': title_font,
        'enemy_obj': enemy_obj,
        'enemy_id': enemy_id,
        'visible': False
    }

    return popup_info


def draw_enemy_popup(screen, popup_info):
    """Draw the enemy ship stats popup window.

    Args:
        screen: Pygame display surface
        popup_info: Popup configuration dictionary from create_enemy_popup
    """
    if not popup_info['visible']:
        return

    enemy = popup_info['enemy_obj']
    rect = popup_info['rect']
    font = popup_info['font']
    small_font = popup_info['small_font']
    title_font = popup_info['title_font']

    popup_surface = pygame.Surface((rect.width, rect.height))
    popup_surface.fill((40, 40, 60))

    # Draw border
    pygame.draw.rect(popup_surface, (100, 100, 150), popup_surface.get_rect(), 3)

    y_offset = 10

    # Ship name and class
    name_text = title_font.render(enemy.ship_name, True, (255, 255, 255))
    popup_surface.blit(name_text, (10, y_offset))
    y_offset += 35

    class_text = small_font.render(f"Class: {enemy.ship_class}", True, (200, 200, 200))
    popup_surface.blit(class_text, (10, y_offset))
    y_offset += 30

    # Position
    pos_text = small_font.render(f"Position: ({enemy.system_q}, {enemy.system_r})", True, (200, 200, 200))
    popup_surface.blit(pos_text, (10, y_offset))
    y_offset += 30

    # Hull integrity
    hull_text = font.render("Hull Integrity:", True, (255, 255, 255))
    popup_surface.blit(hull_text, (10, y_offset))
    y_offset += 25

    hull_percent = (enemy.health / enemy.max_health) * 100
    hull_color = (0, 255, 0) if hull_percent > 60 else (255, 255, 0) if hull_percent > 30 else (255, 0, 0)
    hull_value_text = font.render(f"{enemy.health}/{enemy.max_health} ({hull_percent:.0f}%)", True, hull_color)
    popup_surface.blit(hull_value_text, (20, y_offset))
    y_offset += 35

    # Shields
    shield_text = font.render("Shields:", True, (255, 255, 255))
    popup_surface.blit(shield_text, (10, y_offset))
    y_offset += 25

    shield_percent = (enemy.shields / enemy.max_shields) * 100
    shield_color = (0, 150, 255)
    shield_value_text = font.render(f"{enemy.shields}/{enemy.max_shields} ({shield_percent:.0f}%)", True, shield_color)
    popup_surface.blit(shield_value_text, (20, y_offset))
    y_offset += 35

    # Energy
    energy_text = font.render("Energy:", True, (255, 255, 255))
    popup_surface.blit(energy_text, (10, y_offset))
    y_offset += 25

    energy_percent = (enemy.energy / enemy.max_energy) * 100
    energy_color = (255, 255, 0)
    energy_value_text = font.render(f"{enemy.energy}/{enemy.max_energy} ({energy_percent:.0f}%)", True, energy_color)
    popup_surface.blit(energy_value_text, (20, y_offset))
    y_offset += 35

    # Weapons status
    weapons_text = font.render("Weapons:", True, (255, 255, 255))
    popup_surface.blit(weapons_text, (10, y_offset))
    y_offset += 25

    phaser_status = small_font.render("* Phasers: Online", True, (0, 255, 0))
    popup_surface.blit(phaser_status, (20, y_offset))
    y_offset += 20

    torpedo_status = small_font.render("* Torpedoes: Online", True, (0, 255, 0))
    popup_surface.blit(torpedo_status, (20, y_offset))
    y_offset += 30

    # Threat assessment
    threat_text = font.render("Threat Level:", True, (255, 255, 255))
    popup_surface.blit(threat_text, (10, y_offset))
    y_offset += 25

    if hull_percent > 80:
        threat_level = "HIGH"
        threat_color = (255, 0, 0)
    elif hull_percent > 50:
        threat_level = "MODERATE"
        threat_color = (255, 255, 0)
    else:
        threat_level = "LOW"
        threat_color = (0, 255, 0)

    threat_level_text = font.render(threat_level, True, threat_color)
    popup_surface.blit(threat_level_text, (20, y_offset))

    # Blit popup to main screen
    screen.blit(popup_surface, rect.topleft)


def update_enemy_popups(game_state, systems, enemy_scan_panel, add_event_log):
    """Update and clean up enemy popups for destroyed ships.

    Args:
        game_state: Current game state
        systems: Dictionary of system objects
        enemy_scan_panel: Panel displaying enemy scan results
        add_event_log: Function to add messages to event log
    """
    destroyed_enemies = []
    for enemy_id, popup_info in game_state.scan.enemy_popups.items():
        enemy = popup_info['enemy_obj']
        # Check if enemy is destroyed
        if not hasattr(enemy, 'health') or enemy.health <= 0:
            destroyed_enemies.append(enemy_id)
        # Check if enemy is still in current system
        elif enemy not in systems.get(game_state.current_system, []):
            destroyed_enemies.append(enemy_id)

    # Remove destroyed enemies from tracking
    for enemy_id in destroyed_enemies:
        game_state.remove_enemy_popup(enemy_id)
        game_state.remove_targeted_enemy(enemy_id)
        add_event_log(f"Target {enemy_id} lost - popup closed")
        enemy_scan_panel.remove_scan_result(enemy_id)


def get_enemy_id(enemy_obj, game_state):
    """Get or assign a unique ID to an enemy object.

    Args:
        enemy_obj: The enemy MapObject
        game_state: Current game state

    Returns:
        Unique enemy ID string
    """
    # Check if this enemy already has an ID
    for enemy_id, tracked_enemy in game_state.combat.targeted_enemies.items():
        if tracked_enemy is enemy_obj:
            return enemy_id

    # Assign new ID and track the enemy
    enemy_id = game_state.get_next_enemy_id()
    game_state.add_targeted_enemy(enemy_id, enemy_obj)
    return enemy_id
