import pygame
import math
import sys
import os
import traceback
import logging
import random
import time
import glob

# Adjust the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import debug logger
from debug_logger import log_debug, get_log_path

# No constants are currently used from data.constants, so removing the import

from galaxy_generation.object_placement import place_objects_by_system, generate_system_objects
from ui.hex_map import create_hex_grid_for_map
from ui.button_panel import draw_button_panel, handle_button_events
from ui.stardate import Stardate
from ui.background_loader import BackgroundAndStarLoader
from galaxy_generation.map_object import MapObject
from ui.sound_manager import get_sound_manager
from ui.ship_status_display import create_ship_status_display
from ui.enemy_scan_panel import create_enemy_scan_panel
from ship.player_ship import PlayerShip
from game.game_state import GameState
from data import constants
from data.constants import STARTING_ENERGY, PLAYER_SHIELD_CAPACITY

# Calculate compact window dimensions based on layout needs
RIGHT_EVENT_LOG_WIDTH = 300
SHIP_STATUS_WIDTH = 300     # Ship status panel width
ENEMY_SCAN_WIDTH = 280      # Enemy scan panel width
BOTTOM_PANEL_HEIGHT = 200
STATUS_HEIGHT = 40
# Calculate minimum width needed: map + event log + ship status + enemy scan
map_size = min(980, 960 - STATUS_HEIGHT - BOTTOM_PANEL_HEIGHT)  # Targeting ~720px map
WIDTH = map_size + RIGHT_EVENT_LOG_WIDTH + SHIP_STATUS_WIDTH + ENEMY_SCAN_WIDTH
HEIGHT = 1020

# Pane constants
STATUS_HEIGHT = 40

# Colors
COLOR_BG = (20, 20, 30)
COLOR_STATUS = (60, 60, 100)
COLOR_MAP = (40, 40, 60)
COLOR_EVENT_LOG = (30, 30, 50)
COLOR_EVENT_LOG_BORDER = (80, 80, 120)
COLOR_IMAGE_DISPLAY = (30, 50, 30)
COLOR_CONTROL_PANEL = (50, 30, 30)
COLOR_BUTTON_AREA_BORDER = (80, 50, 50)
COLOR_TEXT = (220, 220, 220)
HEX_OUTLINE = (180, 180, 220)
HEX_BG = (40, 40, 60)
COLOR_MAP_DEBUG = (255, 0, 0)      # Red for map pane
COLOR_GRID_DEBUG = (0, 255, 0)     # Green for grid bounding box

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Star Trek Tactical Game - UI Wireframe')

# Use clean sans-serif system fonts for better readability
font = pygame.font.SysFont('arial', 18)  # Regular font for general text
label_font = pygame.font.SysFont('arial', 16, bold=True)  # Bold font for panel labels
title_font = pygame.font.SysFont('arial', 20)  # Font for titles
small_font = pygame.font.SysFont('arial', 14)  # Small font

# Calculate layout once
# Map size already calculated above
# No extra space - window width exactly fits map + event log
map_x = 0
map_y = STATUS_HEIGHT
bottom_pane_y = map_y + map_size
bottom_pane_height = HEIGHT - bottom_pane_y
image_display_width = map_size // 2
control_panel_width = map_size - image_display_width
# Right event log panel dimensions
event_log_x = map_size
event_log_y = STATUS_HEIGHT
event_log_width = RIGHT_EVENT_LOG_WIDTH
event_log_height = HEIGHT - STATUS_HEIGHT

# Debug layout calculations
# Layout initialized

# TOGGLE_BTN_Y will be calculated after button parameters are defined

# Create the hex grid
hex_grid = create_hex_grid_for_map(map_x, map_y, map_size, 20, 20)

# Create ship status display
ship_status_x = map_size + event_log_width  # To the right of event log
ship_status_y = STATUS_HEIGHT
ship_status_width = SHIP_STATUS_WIDTH
ship_status_height = HEIGHT - STATUS_HEIGHT
ship_status_display = create_ship_status_display(
    ship_status_x, ship_status_y, 
    ship_status_width, ship_status_height, 
    font
)

# Create enemy scan panel to the right of ship status
enemy_scan_x = ship_status_x + SHIP_STATUS_WIDTH  # To the right of ship status
enemy_scan_y = STATUS_HEIGHT
enemy_scan_width = ENEMY_SCAN_WIDTH
enemy_scan_height = HEIGHT - STATUS_HEIGHT
enemy_scan_panel = create_enemy_scan_panel(
    enemy_scan_x, enemy_scan_y,
    enemy_scan_width, enemy_scan_height,
    font
)

# Generate map objects by system (now returns systems, star_coords, lazy_object_coords, planet_orbits)
log_debug("Starting galaxy generation...")
systems, star_coords, lazy_object_coords, planet_orbits = place_objects_by_system()

# Debug output for verification
log_debug(f"Number of stars: {len(star_coords)}")
log_debug(f"Number of planets: {len(planet_orbits)}")
log_debug(f"Star coordinates: {list(star_coords)[:5]}...")  # Show first 5
if planet_orbits:
    log_debug(f"Sample planet orbit: {planet_orbits[0]}")
    # Check which stars have planets
    stars_with_planets = set(orbit['star'] for orbit in planet_orbits)
    log_debug(f"Stars with planets: {stars_with_planets}")

# Debug enemy placement
enemy_coords = lazy_object_coords.get('enemy', [])
log_debug(f"Total enemies placed: {len(enemy_coords)}")
star_systems_with_enemies = [coord for coord in set(enemy_coords) if coord in star_coords]
log_debug(f"Star systems with enemies: {len(star_systems_with_enemies)} out of {len(star_coords)}")
log_debug(f"First 5 star systems with enemies: {star_systems_with_enemies[:5]}")
log_debug(f"First 10 enemy coordinates: {enemy_coords[:10]}")
log_debug(f"Type of lazy_object_coords['enemy']: {type(lazy_object_coords.get('enemy'))}")

# Log which systems should have enemies
log_debug("=== SYSTEMS WITH ENEMIES (from placement) ===")
enemy_system_counts = {}
for coord in enemy_coords:
    enemy_system_counts[coord] = enemy_system_counts.get(coord, 0) + 1
for coord, count in sorted(enemy_system_counts.items())[:10]:
    is_star = coord in star_coords
    has_planets = any(orbit['star'] == coord for orbit in planet_orbits)
    system_type = "STAR+PLANET" if is_star and has_planets else "STAR" if is_star else "EMPTY"
    log_debug(f"  {coord}: {count} enemies ({system_type})")

# Set initial player position from lazy_object_coords['player'] - will be set after GameState creation
player_hexes = list(lazy_object_coords['player'])
if player_hexes:
    ship_q, ship_r = player_hexes[0]
else:
    ship_q, ship_r = 0, 0

# current_system will be set after GameState creation

# Create proper PlayerShip instance with PRD-compliant systems
player_ship = PlayerShip(
    name="USS Enterprise",
    max_shield_strength=PLAYER_SHIELD_CAPACITY,  # Balanced shield capacity for tactical combat
    hull_strength=100,
    energy=STARTING_ENERGY,  # PRD: 1000 units
    max_energy=STARTING_ENERGY,
    position=(ship_q, ship_r)
)

# Player object initialization will be done after GameState creation
print(f"[INIT] star_coords: {star_coords}")
print(f"[INIT] lazy_object_coords: {lazy_object_coords}")
print(f"[INIT] systems: {systems}")

# Initialize game state manager
game_state = GameState()

# Initialize weapon animation manager with combat systems
game_state.initialize_weapon_system(player_ship.combat_manager, player_ship)

# Set initial state from player position
game_state.current_system = (ship_q, ship_r)
current_system = game_state.current_system
game_state.set_ship_position(ship_q, ship_r, hex_grid)

# Ensure systems[current_system] always contains at least a star object
if current_system not in systems or not any(obj.type == 'star' for obj in systems[current_system]):
    print(f"[INIT] Adding missing star object to systems at {current_system}")
    systems[current_system] = [MapObject('star', ship_q, ship_r)]

# Ensure only one player object exists in the starting system
if not any(obj.type == 'player' for obj in systems[current_system]):
    player_obj = MapObject('player', ship_q, ship_r)
    # Give player ship initial system coordinates
    player_obj.system_q = 10  # Center of 20x20 grid
    player_obj.system_r = 10
    systems[current_system].append(player_obj)
else:
    # Ensure existing player has system coordinates
    player_obj = next(obj for obj in systems[current_system] if obj.type == 'player')
    if not hasattr(player_obj, 'system_q') or not hasattr(player_obj, 'system_r'):
        player_obj.system_q = 10  # Center of 20x20 grid
        player_obj.system_r = 10

print(f"[INIT] ship_q: {ship_q}, ship_r: {ship_r}, current_system: {current_system}")

# Button panel parameters
BUTTON_W, BUTTON_H = 110, 35
BUTTON_GAP = 15
TOGGLE_BTN_W, TOGGLE_BTN_H = 130, 35
# Calculate TOGGLE_BTN_Y to fit within the window
# We have 3 buttons (removed End Turn), each 35px tall with 15px gaps
# Add significant spacer (50px) between Control Panel label and buttons
CONTROL_PANEL_LABEL_SPACER = 50
TOGGLE_BTN_Y = bottom_pane_y + CONTROL_PANEL_LABEL_SPACER
BUTTON_COLOR = (100, 100, 180)

# Button rectangles for click detection
button_rects, toggle_btn_rect = [], None

# --- Print button labels and indices at startup ---
# Button labels (removed End Turn button)
button_labels = ["Move", "Fire", "Torpedo", "Scan"]
# Button labels ready: ["Move", "Fire", "Torpedo", "Scan"]

# Trajectory start position for mid-flight destination changes (kept as local variables)
trajectory_start_x, trajectory_start_y = None, None

# Calculate max distance for ship speed
corner1 = hex_grid.get_hex_center(0, 0)
corner2 = hex_grid.get_hex_center(19, 19)
max_distance = math.hypot(corner2[0] - corner1[0], corner2[1] - corner1[1])

FPS = 60
SHIP_SPEED = max_distance / (2 * FPS)  # pixels per frame for 2s travel

# Game timing
clock = pygame.time.Clock()
move_frames = 2 * FPS  # 2 seconds at 60 FPS

# Stardate system
stardate_system = Stardate()

# Background and star image loader
background_and_star_loader = BackgroundAndStarLoader()


# Event log for displaying messages
EVENT_LOG_MAX_LINES = 25  # Increased to accommodate wrapped text

event_log = []

# Track last system for debug print
last_debug_system = None

# Enemy targeting system
# Enemy and combat variables now managed by game_state

# Planet animation state dictionary
planet_anim_state = { (orbit['star'], orbit['planet']): orbit['angle'] for orbit in planet_orbits }
# Planet color storage
planet_colors = {}
# Planet image storage
planet_images_assigned = {}  # Dictionary: (star, planet) -> (image, scaled_image, size_multiplier)

# Color generation functions
def get_star_color():
    """Generate realistic star colors based on stellar classification."""
    star_colors = [
        (255, 255, 255),  # White (white dwarf, hot stars)
        (255, 254, 250),  # Blue-white
        (255, 255, 224),  # Yellow-white 
        (255, 255, 0),    # Yellow (like our Sun)
        (255, 204, 0),    # Yellow-orange
        (255, 178, 0),    # Orange
        (255, 128, 0),    # Deep orange
        (255, 64, 0),     # Red-orange
        (255, 0, 0),      # Red (red giant/dwarf)
        (200, 0, 0),      # Deep red
    ]
    return random.choice(star_colors)

def get_planet_color():
    """Generate realistic planet colors."""
    planet_colors = [
        (139, 90, 43),    # Brown (rocky/desert)
        (160, 82, 45),    # Sienna brown
        (34, 139, 34),    # Forest green (vegetated)
        (0, 100, 0),      # Dark green
        (30, 144, 255),   # Dodger blue (water world)
        (0, 191, 255),    # Deep sky blue
        (70, 130, 180),   # Steel blue (ice world)
        (178, 34, 34),    # Rust red (Mars-like)
        (205, 92, 92),    # Indian red
        (188, 143, 143),  # Rosy brown
    ]
    return random.choice(planet_colors)

def create_enemy_popup(enemy_id, enemy_obj):
    """Create a popup window for enemy ship stats."""
    # Calculate popup window dimensions and position
    popup_width = 280
    popup_height = 350
    # Position popups in the dedicated dock area
    popup_dock_x = map_size + RIGHT_EVENT_LOG_WIDTH  # Start of popup dock area
    popup_x = popup_dock_x + 10  # 10px padding from dock edge
    popup_y = STATUS_HEIGHT + 50 + (len(enemy_popups) * (popup_height + 10))  # Stack vertically below "Scan Results" label
    
    # Initialize enemy stats if not present (using consistent values with player ship)
    if not hasattr(enemy_obj, 'health'):
        enemy_obj.health = 100  # Same as player ship hull strength
    if not hasattr(enemy_obj, 'max_health'):
        enemy_obj.max_health = 100
    if not hasattr(enemy_obj, 'energy'):
        enemy_obj.energy = 1000  # Same as player ship starting energy
    if not hasattr(enemy_obj, 'max_energy'):
        enemy_obj.max_energy = 1000
    if not hasattr(enemy_obj, 'shields'):
        enemy_obj.shields = ENEMY_SHIELD_CAPACITY  # Substantial shield capacity for tactical combat
    if not hasattr(enemy_obj, 'max_shields'):
        enemy_obj.max_shields = ENEMY_SHIELD_CAPACITY
    if not hasattr(enemy_obj, 'ship_name'):
        enemy_obj.ship_name = f"Enemy Vessel {enemy_id}"
    if not hasattr(enemy_obj, 'ship_class'):
        ship_classes = ["Klingon Bird of Prey", "Romulan Warbird", "Gorn Destroyer", "Tholian Web Spinner"]
        enemy_obj.ship_class = random.choice(ship_classes)
    
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

def draw_enemy_popup(popup_info):
    """Draw the enemy ship stats popup window."""
    if not popup_info['visible']:
        return
    
    enemy = popup_info['enemy_obj']
    rect = popup_info['rect']
    font = popup_info['font']
    small_font = popup_info['small_font']
    title_font = popup_info['title_font']
    
    # Create a separate surface for the popup (if we want to move it outside main window later)
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
    
    phaser_status = small_font.render("• Phasers: Online", True, (0, 255, 0))
    popup_surface.blit(phaser_status, (20, y_offset))
    y_offset += 20
    
    torpedo_status = small_font.render("• Torpedoes: Online", True, (0, 255, 0))
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
    
    # Blit popup to main screen in the designated dock area
    screen.blit(popup_surface, rect.topleft)

def update_enemy_popups():
    """Update and clean up enemy popups for destroyed ships."""
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
        game_state.add_event_log(f"Target {enemy_id} lost - popup closed")
        # Remove from enemy scan panel
        enemy_scan_panel.remove_scan_result(enemy_id)

def get_enemy_id(enemy_obj):
    """Get or assign a unique ID to an enemy object."""
    # Check if this enemy already has an ID
    for enemy_id, tracked_enemy in game_state.combat.targeted_enemies.items():
        if tracked_enemy is enemy_obj:
            return enemy_id
    
    # Assign new ID and track the enemy
    enemy_id = game_state.get_next_enemy_id()
    game_state.add_targeted_enemy(enemy_id, enemy_obj)
    return enemy_id

def perform_enemy_scan(enemy_obj, enemy_id):
    """Perform a detailed scan of an enemy and add results to scan panel."""
    import random
    import math
    
    # Calculate distance from player
    player_obj = next((obj for obj in systems.get(game_state.current_system, []) if obj.type == 'player'), None)
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
    
    # Generate scan data based on enemy position (deterministic for consistency)
    seed = enemy_obj.system_q * 1000 + enemy_obj.system_r
    random.seed(seed)
    
    enemy_name = random.choice(enemy_types)
    
    # Use balanced maximum values for tactical combat
    max_hull = ENEMY_HULL_STRENGTH  # Hull integrity
    max_shields = ENEMY_SHIELD_CAPACITY  # Substantial shields that require multiple hits
    max_energy = 1000  # Energy systems
    
    # Enemies start at full strength but may have some minor battle damage
    current_hull = random.randint(int(max_hull * 0.85), max_hull)  # 85-100% hull
    current_shields = random.randint(int(max_shields * 0.8), max_shields)  # 80-100% shields  
    current_energy = random.randint(int(max_energy * 0.8), max_energy)  # 80-100% energy
    
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
    
    # Generate weapon list
    weapons = []
    if random.random() > 0.2:  # 80% have phasers
        weapons.append("Disruptor Arrays")
    if random.random() > 0.4:  # 60% have torpedoes
        weapons.append("Photon Torpedoes")
    if random.random() > 0.8:  # 20% have special weapons
        weapons.append("Plasma Cannons")
    
    # Reset random seed
    random.seed()
    
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
        'threat_level': threat_level
    }
    
    # Add to enemy scan panel
    enemy_scan_panel.add_scan_result(enemy_id, scan_data)
    
    # Log the scan
    add_event_log(f"Scanning {enemy_name} - Range: {distance:.1f}km, Threat: {threat_level}")
    
    # Play scan sound
    sound_manager.play_sound('scanner')

def get_enemy_current_position(enemy_obj, hex_grid):
    """Get the current position of an enemy (animated if moving, otherwise static)"""
    if hasattr(enemy_obj, 'anim_px') and hasattr(enemy_obj, 'anim_py'):
        # Enemy has animated pixel position - return it directly
        return (enemy_obj.anim_px, enemy_obj.anim_py)
    elif hasattr(enemy_obj, 'system_q') and hasattr(enemy_obj, 'system_r'):
        # Enemy has static hex position - convert to pixels
        return hex_grid.get_hex_center(enemy_obj.system_q, enemy_obj.system_r)
    else:
        # Fallback to origin
        return hex_grid.get_hex_center(0, 0)

def update_enemy_scan_positions():
    """Update scan panel positions for all scanned enemies that are moving"""
    for enemy_id, scan_data in enemy_scan_panel.scanned_enemies.items():
        # Find the actual enemy object by ID in current system
        for obj in systems.get(game_state.current_system, []):
            if obj.type == 'enemy' and get_enemy_id(obj) == enemy_id:
                # Update scan data position if enemy has moved
                # Use the enemy ship's actual hex position instead of trying to convert pixels
                enemy_ship_id = id(obj)
                if enemy_ship_id in player_ship.combat_manager.enemy_ships:
                    enemy_ship = player_ship.combat_manager.enemy_ships[enemy_ship_id]
                    current_hex_pos = enemy_ship.position  # This is the actual hex coordinate
                    
                    if current_hex_pos != scan_data['position']:
                        scan_data['position'] = current_hex_pos
                        
                        # Recalculate distance and bearing from player
                        player_obj = next((o for o in systems.get(game_state.current_system, []) if o.type == 'player'), None)
                        if player_obj and hasattr(player_obj, 'system_q') and hasattr(player_obj, 'system_r'):
                            dx = current_hex_pos[0] - player_obj.system_q  
                            dy = current_hex_pos[1] - player_obj.system_r
                            scan_data['distance'] = math.sqrt(dx * dx + dy * dy)
                            bearing = math.degrees(math.atan2(dy, dx))
                            if bearing < 0:
                                bearing += 360
                            scan_data['bearing'] = bearing
                break

# Helper functions for multi-hex objects
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
            hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
            orbit_radius_px = orbit['hex_radius'] * hex_size
            key = (orbit['star'], orbit['planet'])
            angle = planet_anim_state.get(key, orbit['angle'])
            planet_px = star_px + orbit_radius_px * math.cos(angle)
            planet_py = star_py + orbit_radius_px * math.sin(angle)
            # Convert planet pixel position to hex
            planet_q, planet_r = hex_grid.pixel_to_hex(planet_px, planet_py)
            if planet_q is not None and planet_r is not None:
                planet_hexes = get_planet_hexes(planet_q, planet_r)
                if (q, r) in planet_hexes:
                    return True, 'planet'
    
    return False, None

def show_orbit_dialog(screen, font):
    """Show a popup dialog asking if player wants to orbit the planet."""
    # Dialog dimensions
    dialog_width = 400
    dialog_height = 150
    screen_width, screen_height = screen.get_size()
    dialog_x = (screen_width - dialog_width) // 2
    dialog_y = (screen_height - dialog_height) // 2
    
    # Colors
    dialog_bg = (50, 50, 50)
    dialog_border = (200, 200, 200)
    button_bg = (100, 100, 100)
    button_hover = (150, 150, 150)
    text_color = (255, 255, 255)
    
    # Button dimensions
    button_width = 80
    button_height = 40
    yes_button_x = dialog_x + 80
    no_button_x = dialog_x + 240
    button_y = dialog_y + 90
    
    clock = pygame.time.Clock()
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        # Check button hover states
        yes_hover = (yes_button_x <= mouse_pos[0] <= yes_button_x + button_width and
                    button_y <= mouse_pos[1] <= button_y + button_height)
        no_hover = (no_button_x <= mouse_pos[0] <= no_button_x + button_width and
                   button_y <= mouse_pos[1] <= button_y + button_height)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if yes_hover:
                        return True
                    elif no_hover:
                        return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    return False
        
        # Draw dialog background
        pygame.draw.rect(screen, dialog_bg, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(screen, dialog_border, (dialog_x, dialog_y, dialog_width, dialog_height), 2)
        
        # Draw text
        title_text = font.render("Planet Detected", True, text_color)
        title_rect = title_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 30))
        screen.blit(title_text, title_rect)
        
        message_text = font.render("Maintain orbit around this planet?", True, text_color)
        message_rect = message_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 60))
        screen.blit(message_text, message_rect)
        
        # Draw buttons
        yes_color = button_hover if yes_hover else button_bg
        no_color = button_hover if no_hover else button_bg
        
        pygame.draw.rect(screen, yes_color, (yes_button_x, button_y, button_width, button_height))
        pygame.draw.rect(screen, dialog_border, (yes_button_x, button_y, button_width, button_height), 1)
        
        pygame.draw.rect(screen, no_color, (no_button_x, button_y, button_width, button_height))
        pygame.draw.rect(screen, dialog_border, (no_button_x, button_y, button_width, button_height), 1)
        
        # Button text
        yes_text = font.render("Yes (Y)", True, text_color)
        yes_text_rect = yes_text.get_rect(center=(yes_button_x + button_width // 2, button_y + button_height // 2))
        screen.blit(yes_text, yes_text_rect)
        
        no_text = font.render("No (N)", True, text_color)
        no_text_rect = no_text.get_rect(center=(no_button_x + button_width // 2, button_y + button_height // 2))
        screen.blit(no_text, no_text_rect)
        
        pygame.display.flip()
        clock.tick(60)

# --- System map movement state ---
system_ship_anim_x = None
system_ship_anim_y = None
system_dest_q = None
system_dest_r = None

# --- System movement state (local to system mode) ---
player_orbit_key = None     # (star, planet) key to track which planet we're orbiting
player_orbit_speed = 0.4    # Radians per second (reduced for more realistic movement)
system_ship_moving = False
system_move_start_time = None
system_move_duration_ms = 1000  # 1 second for system moves

# --- Pending orbital state (for movement-then-orbit transitions) ---
pending_orbit_center = None    # (x, y) position of planet to orbit when movement completes
pending_orbit_key = None       # (star, planet) key for the pending orbit

# System trajectory start position for mid-flight destination changes
system_trajectory_start_x, system_trajectory_start_y = None, None

# --- Phaser animation constants ---
phaser_anim_duration = 500  # ms
phaser_pulse_count = 5
# Use constants for phaser damage
from data.constants import (PLAYER_PHASER_POWER, PLAYER_PHASER_RANGE, 
                            PHASER_CLOSE_RANGE, PHASER_MEDIUM_RANGE,
                            PHASER_CLOSE_MULTIPLIER, PHASER_MEDIUM_MULTIPLIER, PHASER_LONG_MULTIPLIER,
                            PLAYER_SHIELD_CAPACITY, ENEMY_SHIELD_CAPACITY, ENEMY_HULL_STRENGTH)
phaser_range = PLAYER_PHASER_RANGE

def wrap_text(text, max_width, font):
    """Wrap text to fit within max_width pixels"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        text_width = font.size(test_line)[0]
        
        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word is too long, just add it anyway
                lines.append(word)
    
    if current_line:
        lines.append(current_line)
    
    return lines

def add_event_log(message):
    # Split on newlines and handle each part
    for line in message.split('\n'):
        if line.strip():  # Only add non-empty lines
            game_state.add_event_log(line.strip(), EVENT_LOG_MAX_LINES)

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

# Initialize sound manager
sound_manager = get_sound_manager()

# Start background music
sound_manager.play_background_music()

def process_enemy_weapon_animations(systems, current_system, hex_grid, weapon_animation_manager):
    """Process pending enemy weapon animations and trigger visual effects"""
    if current_system not in systems:
        return
    
    # Find player position for targeting
    player_obj = next((obj for obj in systems[current_system] if obj.type == 'player'), None)
    if not player_obj:
        return
    
    player_pixel_pos = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
    
    # Check all enemies for pending weapon animations
    enemy_count = 0
    animations_processed = 0
    for obj in systems[current_system]:
        if obj.type == 'enemy':
            enemy_count += 1
            # Get enemy ship from combat manager
            enemy_ship_id = id(obj)
            if (hasattr(player_ship, 'combat_manager') and 
                enemy_ship_id in player_ship.combat_manager.enemy_ships):
                
                enemy_ship = player_ship.combat_manager.enemy_ships[enemy_ship_id]
                pending_animations = enemy_ship.get_pending_weapon_animations()
                
                if pending_animations:
                    print(f"[ANIMATION DEBUG] Processing {len(pending_animations)} weapon animations from {enemy_ship.name}")
                
                for animation in pending_animations:
                    animations_processed += 1
                    # Get enemy position 
                    enemy_pixel_pos = hex_grid.get_hex_center(obj.system_q, obj.system_r)
                    
                    print(f"[ANIMATION DEBUG] Starting {animation['weapon_type']} animation with {animation['damage']} damage")
                    
                    if animation['weapon_type'] == 'phaser':
                        # Start enemy phaser animation
                        weapon_animation_manager.enemy_fire_phaser(
                            enemy_ship, enemy_pixel_pos, player_pixel_pos, animation['damage']
                        )
                    elif animation['weapon_type'] == 'torpedo':
                        # Start enemy torpedo animation  
                        weapon_animation_manager.enemy_fire_torpedo(
                            enemy_ship, enemy_pixel_pos, player_pixel_pos, animation['damage']
                        )
    
    # Debug info every few seconds
    import time
    if not hasattr(process_enemy_weapon_animations, '_last_debug') or time.time() - process_enemy_weapon_animations._last_debug > 10.0:
        print(f"[ANIMATION DEBUG] Processed {animations_processed} animations from {enemy_count} enemies in system {current_system}")
        process_enemy_weapon_animations._last_debug = time.time()

# Add initial welcome message
add_event_log("Welcome to Star Trek Tactical Game")
add_event_log("Click to navigate, scan for objects")

try:
    running = True
    while running:
        screen.fill(COLOR_BG)
        
        # Update weapon animations and handle combat events
        current_time = pygame.time.get_ticks()
        weapon_events = game_state.weapon_animation_manager.update(current_time, hex_grid)
        
        # Update enemy weapon animations
        game_state.weapon_animation_manager.update_enemy_animations(current_time)
        
        # Process pending enemy weapon animations
        process_enemy_weapon_animations(systems, game_state.current_system, hex_grid, game_state.weapon_animation_manager)
        
        # Handle weapon combat events
        if weapon_events['phaser_completed']:
            phaser_event = weapon_events['phaser_completed']
            combat_result = phaser_event['damage_info']
            updated_result = phaser_event['combat_result']
            
            # Log damage results
            if combat_result['shield_damage'] > 0 and combat_result['hull_damage'] > 0:
                add_event_log(f"Phaser hit! Range: {combat_result['distance']:.1f} hexes - Shields: {combat_result['shield_damage']} Hull: {combat_result['hull_damage']}")
            elif combat_result['shield_damage'] > 0:
                add_event_log(f"Phaser hit shields! Range: {combat_result['distance']:.1f} hexes - Damage: {combat_result['shield_damage']}")
            elif combat_result['hull_damage'] > 0:
                add_event_log(f"Hull breach! Range: {combat_result['distance']:.1f} hexes - Damage: {combat_result['hull_damage']}")
            elif combat_result['damage_calculated'] > 0:
                add_event_log(f"Phaser hit! Range: {combat_result['distance']:.1f} hexes - Absorbed by shields")
            else:
                add_event_log(f"Phaser beam too weak! Range: {combat_result['distance']:.1f} hexes - Increase power allocation")
            
            # Update scan panel
            enemy_id = None
            for eid, enemy_obj in game_state.combat.targeted_enemies.items():
                if enemy_obj is phaser_event['target_enemy']:
                    enemy_id = eid
                    break
            
            if enemy_id and enemy_id in enemy_scan_panel.scanned_enemies:
                enemy_scan_panel.scanned_enemies[enemy_id]['hull'] = updated_result['target_health']
                enemy_scan_panel.scanned_enemies[enemy_id]['max_hull'] = updated_result['target_max_health']
                enemy_scan_panel.scanned_enemies[enemy_id]['shields'] = updated_result['target_shields']
                enemy_scan_panel.scanned_enemies[enemy_id]['max_shields'] = updated_result['target_max_shields']
            
            # Check if target destroyed
            if combat_result['target_destroyed']:
                add_event_log("Enemy ship destroyed!")
                systems[current_system].remove(phaser_event['target_enemy'])
                if enemy_id:
                    enemy_scan_panel.remove_scan_result(enemy_id)
                game_state.combat.selected_enemy = None
        
        if weapon_events['torpedo_ring_hits']:
            ring_event = weapon_events['torpedo_ring_hits']
            newly_hit_enemies = ring_event['newly_hit_enemies']
            explosion_center = ring_event['explosion_center']
            
            for result in newly_hit_enemies:
                enemy = result['enemy']
                ring_index = result['ring_index']
                damage = result['damage']
                distance_pixels = result['distance_pixels']
                updated_result = result['combat_result']
                
                # Define ring names for better logging
                ring_names = ["Core Blast", "Primary Wave", "Secondary Wave", "Tertiary Wave", "Pressure Wave", "Outer Shockwave"]
                ring_name = ring_names[min(ring_index, len(ring_names)-1)]
                
                # Log the ring hit with descriptive text
                add_event_log(f"Torpedo {ring_name} hit enemy ship! Distance: {distance_pixels:.0f}px - Damage: {damage}")
                
                # Update scan panel for this enemy
                enemy_id = None
                for eid, enemy_obj in game_state.combat.targeted_enemies.items():
                    if enemy_obj is enemy:
                        enemy_id = eid
                        break
                
                if enemy_id and enemy_id in enemy_scan_panel.scanned_enemies:
                    enemy_scan_panel.scanned_enemies[enemy_id]['hull'] = updated_result['target_health']
                    enemy_scan_panel.scanned_enemies[enemy_id]['max_hull'] = getattr(enemy, 'max_health', constants.ENEMY_HULL_STRENGTH)
                    enemy_scan_panel.scanned_enemies[enemy_id]['shields'] = updated_result['target_shields']
                    enemy_scan_panel.scanned_enemies[enemy_id]['max_shields'] = getattr(enemy, 'max_shields', constants.ENEMY_SHIELD_CAPACITY)
                
                # Check if this enemy was destroyed
                if updated_result.get('target_destroyed', False):
                    add_event_log(f"Enemy ship destroyed by {ring_name}!")
                    if enemy in systems[current_system]:
                        systems[current_system].remove(enemy)
                    if enemy_id:
                        enemy_scan_panel.remove_scan_result(enemy_id)
                        if enemy_id in game_state.combat.targeted_enemies:
                            del game_state.combat.targeted_enemies[enemy_id]
                        if enemy_id in game_state.scan.enemy_popups:
                            del game_state.scan.enemy_popups[enemy_id]
                    if game_state.combat.selected_enemy is enemy:
                        game_state.combat.selected_enemy = None
        # Status/Tooltip Panel (top)
        status_rect = pygame.Rect(0, 0, WIDTH, STATUS_HEIGHT)
        pygame.draw.rect(screen, COLOR_STATUS, status_rect)
        status_label = label_font.render('Status/Tooltip Panel', True, COLOR_TEXT)
        screen.blit(status_label, (10, 8))
        # Weapon Cooldown Display (just left of stardate)
        cooldown_y = 8
        cooldown_x = WIDTH - 320
        
        # Phaser Cooldown
        if hasattr(player_ship, 'phaser_system') and player_ship.phaser_system.is_on_cooldown():
            cooldown_time = (player_ship.phaser_system._last_fired_time + player_ship.phaser_system.cooldown_seconds) - time.time()
            if cooldown_time > 0:
                cooldown_label = font.render(f"Phasers: {cooldown_time:.1f}s", True, (255, 255, 0))  # Yellow color
                screen.blit(cooldown_label, (cooldown_x, cooldown_y))
                cooldown_y += 20  # Move next cooldown down
        
        # Torpedo Cooldown
        if hasattr(player_ship, 'torpedo_system') and player_ship.torpedo_system.is_on_cooldown():
            cooldown_time = (player_ship.torpedo_system._last_fired_time + player_ship.torpedo_system.cooldown_seconds) - time.time()
            if cooldown_time > 0:
                cooldown_label = font.render(f"Torpedoes: {cooldown_time:.1f}s", True, (255, 100, 100))  # Reddish color
                screen.blit(cooldown_label, (cooldown_x, cooldown_y))
        
        # Stardate Display
        stardate_label = font.render(stardate_system.format_stardate(), True, COLOR_TEXT)
        screen.blit(stardate_label, (WIDTH - 180, 8))

        # Main Map Area (perfect square, flush left)
        map_rect = pygame.Rect(map_x, map_y, map_size, map_size)
        pygame.draw.rect(screen, COLOR_MAP, map_rect)

        # --- Removed map mode label as requested ---

        # Draw background image (lowest layer)
        background_img = background_and_star_loader.get_scaled_background(map_size, map_size)
        if background_img:
            screen.blit(background_img, (map_x, map_y))

        # Draw stars in background (before hex grid) for system view
        if game_state.map_mode == 'system':
            # Draw stars that occupy 4 hexes - in background
            for obj in systems.get(game_state.current_system, []):
                if obj.type == 'star':
                    if not hasattr(obj, 'system_q') or not hasattr(obj, 'system_r'):
                        obj.system_q = random.randint(1, hex_grid.cols - 2)
                        obj.system_r = random.randint(1, hex_grid.rows - 2)
                    # Draw star across multiple hexes
                    star_hexes = get_star_hexes(obj.system_q, obj.system_r)
                    # Calculate center of mass for the star
                    sum_x, sum_y = 0, 0
                    valid_hexes = []
                    for hq, hr in star_hexes:
                        if 0 <= hq < hex_grid.cols and 0 <= hr < hex_grid.rows:
                            hx, hy = hex_grid.get_hex_center(hq, hr)
                            sum_x += hx
                            sum_y += hy
                            valid_hexes.append((hx, hy))
                    if valid_hexes:
                        center_x = sum_x / len(valid_hexes)
                        center_y = sum_y / len(valid_hexes)
                        # Get or assign star image
                        if not hasattr(obj, 'star_image'):
                            # Assign a random star image to this star object
                            obj.star_image = background_and_star_loader.get_random_star_image()
                            obj.scaled_star_image = None  # Will be scaled when needed
                        
                        # Draw star image if available, otherwise fallback to circle
                        if obj.star_image:
                            # Scale image if not already done or if radius changed
                            if obj.scaled_star_image is None:
                                obj.scaled_star_image = background_and_star_loader.scale_star_image(obj.star_image, hex_grid.radius * 3.6)
                            
                            if obj.scaled_star_image:
                                # Center the image
                                image_rect = obj.scaled_star_image.get_rect()
                                image_rect.center = (int(center_x), int(center_y))
                                screen.blit(obj.scaled_star_image, image_rect)
                            else:
                                # Fallback to circle if image scaling failed
                                if not hasattr(obj, 'color'):
                                    obj.color = get_star_color()
                                pygame.draw.circle(screen, obj.color, (int(center_x), int(center_y)), int(hex_grid.radius * 3.6))
                        else:
                            # Fallback to circle if no image available
                            if not hasattr(obj, 'color'):
                                obj.color = get_star_color()
                            pygame.draw.circle(screen, obj.color, (int(center_x), int(center_y)), int(hex_grid.radius * 3.6))

        # Draw the hex grid with conditional transparency based on map mode
        # Sector map: More visible for fog of war navigation, System map: Barely visible for clean aesthetics
        grid_alpha = 64 if game_state.map_mode == 'sector' else 20
        hex_grid.draw_grid(screen, HEX_OUTLINE, alpha=grid_alpha)

        # --- FOG OF WAR OVERLAY (draw early to hide objects) ---
        # Only apply fog of war to sector map, not system maps
        if game_state.map_mode == 'sector':
            for row in range(hex_grid.rows):
                for col in range(hex_grid.cols):
                    if (col, row) not in game_state.scan.scanned_systems:
                        cx, cy = hex_grid.get_hex_center(col, row)
                        hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=153)

        # Calculate delta time for smooth ship rotation
        delta_time = clock.get_time() / 1000.0  # Convert milliseconds to seconds

        # Draw objects on the grid
        if game_state.map_mode == 'sector':
            # Only draw system indicators if a sector scan has been done
            if game_state.scan.sector_scan_active:
                # Show indicator for any hex that has actual systems (not individual planets)
                # Stars have systems, lazy objects have systems, but planets orbit around stars elsewhere
                occupied_hexes = set(star_coords)
                for coords_set in lazy_object_coords.values():
                    occupied_hexes.update(coords_set)
                
                # Ensure starbase systems are generated for sector map display
                if 'starbase' in lazy_object_coords:
                    for starbase_coord in lazy_object_coords['starbase']:
                        if starbase_coord not in systems:
                            # Generate the missing starbase system
                            from galaxy_generation.object_placement import generate_system_objects
                            starbase_objects = generate_system_objects(
                                starbase_coord[0], starbase_coord[1],
                                lazy_object_coords,
                                star_coords=star_coords,
                                planet_orbits=planet_orbits,
                                grid_size=hex_grid.cols
                            )
                            systems[starbase_coord] = starbase_objects
                
                # NOTE: Don't add planet coordinates - they orbit around stars, they don't have their own systems
                green_dots_drawn = 0
                for q, r in occupied_hexes:
                    px, py = hex_grid.get_hex_center(q, r)
                    
                    # Check if this system contains a starbase - use light green if so
                    system_has_starbase = False
                    system_objects = systems.get((q, r), [])
                    for obj in system_objects:
                        if obj.type == 'starbase':
                            system_has_starbase = True
                            break
                    
                    # Draw dot with appropriate color
                    dot_color = (144, 238, 144) if system_has_starbase else (100, 100, 130)  # Light green for starbase, default for others
                    pygame.draw.circle(
                        screen, dot_color, (int(px), int(py)), 6
                    )
        else:
            # Ensure we have objects for the current system (generate but don't show until scanned)
            if current_system not in systems:
                # Debug check before generation
                expected_enemies = lazy_object_coords.get('enemy', []).count(current_system)
                is_star = current_system in star_coords
                has_planets = any(orbit['star'] == current_system for orbit in planet_orbits)
                add_event_log(f"[RENDER GEN] Generating system {current_system}")
                add_event_log(f"[RENDER GEN] Type: {'STAR+PLANET' if is_star and has_planets else 'STAR' if is_star else 'EMPTY'}")
                add_event_log(f"[RENDER GEN] Expected enemies: {expected_enemies}")
                
                # Debug: Check the exact data being passed
                if expected_enemies > 0:
                    log_debug(f"[RENDER] System {current_system} should have {expected_enemies} enemies")
                    add_event_log(f"[DEBUG] Checking lazy_object_coords['enemy'] type: {type(lazy_object_coords.get('enemy'))}")
                    enemy_list = lazy_object_coords.get('enemy', [])
                    if enemy_list:
                        add_event_log(f"[DEBUG] Enemy list length: {len(enemy_list)}")
                        add_event_log(f"[DEBUG] Count of {current_system} in list: {enemy_list.count(current_system)}")
                        log_debug(f"[RENDER] Enemy list contains {current_system}: {enemy_list.count(current_system)} times")
                    else:
                        add_event_log(f"[DEBUG] Enemy list is empty or None!")
                        log_debug(f"[RENDER] ERROR: Enemy list is empty or None!")
                
                # Generate objects for this system if they don't exist
                log_debug(f"[RENDER] Calling generate_system_objects for {current_system}")
                system_objs = generate_system_objects(
                    current_system[0],
                    current_system[1],
                    lazy_object_coords,
                    star_coords=star_coords,
                    planet_orbits=planet_orbits,
                    grid_size=hex_grid.cols
                )
                # Assign random system positions to all objects, avoiding collisions
                placed_objects = []
                for obj in system_objs:
                    if obj.type == 'star':
                        # Stars need more space, place them away from edges
                        obj.system_q = random.randint(2, hex_grid.cols - 3)
                        obj.system_r = random.randint(2, hex_grid.rows - 3)
                        placed_objects.append(obj)
                    else:
                        # For other objects, find unblocked positions
                        max_attempts = 50
                        placed = False
                        for _ in range(max_attempts):
                            q = random.randint(0, hex_grid.cols - 1)
                            r = random.randint(0, hex_grid.rows - 1)
                            # Check if blocked by previously placed objects
                            blocked = False
                            for placed_obj in placed_objects:
                                if placed_obj.type == 'star':
                                    star_hexes = get_star_hexes(placed_obj.system_q, placed_obj.system_r)
                                    if (q, r) in star_hexes:
                                        blocked = True
                                        break
                                elif hasattr(placed_obj, 'system_q') and placed_obj.system_q == q and placed_obj.system_r == r:
                                    blocked = True
                                    break
                            if not blocked:
                                obj.system_q = q
                                obj.system_r = r
                                placed_objects.append(obj)
                                placed = True
                                break
                        if not placed:
                            # Fallback: find any free hex
                            for q in range(hex_grid.cols):
                                for r in range(hex_grid.rows):
                                    blocked = False
                                    for placed_obj in placed_objects:
                                        if placed_obj.type == 'star':
                                            star_hexes = get_star_hexes(placed_obj.system_q, placed_obj.system_r)
                                            if (q, r) in star_hexes:
                                                blocked = True
                                                break
                                        elif hasattr(placed_obj, 'system_q') and placed_obj.system_q == q and placed_obj.system_r == r:
                                            blocked = True
                                            break
                                    if not blocked:
                                        obj.system_q = q
                                        obj.system_r = r
                                        placed_objects.append(obj)
                                        placed = True
                                        break
                                if placed:
                                    break
                systems[current_system] = system_objs
                logging.info(f"[RENDER] Generated {len(system_objs)} objects for system {current_system}")
                
                # Debug: Show what was generated (one-time only)
                add_event_log(f"[RENDER GEN] Generated {len(system_objs)} objects")
                obj_counts = {}
                for obj in system_objs:
                    obj_counts[obj.type] = obj_counts.get(obj.type, 0) + 1
                add_event_log(f"[RENDER GEN] Objects: {dict(obj_counts)}")
                
                # Check for missing enemies
                actual_enemies = obj_counts.get('enemy', 0)
                if expected_enemies > 0 and actual_enemies == 0:
                    add_event_log(f"[RENDER GEN] WARNING: Expected {expected_enemies} enemies but got {actual_enemies}!")
            
            # Draw all objects (fog of war removed for system maps)
            # Note: Stars are now drawn in background before hex grid
                
            # Animate and draw all planets associated with stars in this system
            planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
            if last_debug_system != current_system:
                last_debug_system = current_system
            
            for orbit in planets_in_system:
                # Get star position in system coordinates
                star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
                if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
                    star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
                else:
                    # This shouldn't happen - log error
                    print(f"[ERROR] No star object found in system {current_system} for planet orbit!")
                    star_px, star_py = hex_grid.get_hex_center(current_system[0], current_system[1])
                
                hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
                # Use full orbital radius without reduction to maintain proper separation
                orbit_radius_px = orbit['hex_radius'] * hex_size
                key = (orbit['star'], orbit['planet'])
                # Convert milliseconds to seconds for smooth animation
                dt = clock.get_time() / 1000.0
                # Update angle based on speed (radians per second)
                planet_anim_state[key] += orbit['speed'] * dt
                angle = planet_anim_state[key]
                planet_px = star_px + orbit_radius_px * math.cos(angle)
                planet_py = star_py + orbit_radius_px * math.sin(angle)
                
                # Draw planet at exact orbital position (no hex snapping)
                planet_key = (orbit['star'], orbit['planet'])
                
                # Get or assign planet image and size for maximum variety
                if planet_key not in planet_images_assigned:
                    # Assign a random planet image for maximum variety
                    planet_image = background_and_star_loader.get_random_planet_image()
                    # Assign random size: 1.0 (minimum/current size) to 3.3 (roughly 2 hex widths)
                    size_multiplier = random.uniform(1.0, 3.3)
                    scaled_planet_image = None
                    if planet_image:
                        scaled_planet_image = background_and_star_loader.scale_planet_image(
                            planet_image, hex_grid.radius * 1.8, size_multiplier
                        )
                    planet_images_assigned[planet_key] = (planet_image, scaled_planet_image, size_multiplier)
                    logging.debug(f"[PLANETS] Assigned random planet image to {planet_key} with size multiplier {size_multiplier:.2f}")
                else:
                    planet_image, scaled_planet_image, size_multiplier = planet_images_assigned[planet_key]
                
                # Draw planet image if available, otherwise fallback to circle
                if scaled_planet_image:
                    # Center the planet image
                    image_rect = scaled_planet_image.get_rect()
                    image_rect.center = (int(planet_px), int(planet_py))
                    screen.blit(scaled_planet_image, image_rect)
                else:
                    # Fallback to circle if no image available
                    if planet_key not in planet_colors:
                        planet_colors[planet_key] = get_planet_color()
                    planet_color = planet_colors[planet_key]
                    # Use the same variable sizing for consistency
                    base_radius = hex_grid.radius * 1.8 * 0.6  # Base size
                    variable_radius = int(base_radius * size_multiplier)
                    pygame.draw.circle(screen, planet_color, (int(planet_px), int(planet_py)), variable_radius)
            
            # Draw other objects (starbase, enemy, anomaly, player) with system positions
            for obj in systems.get(current_system, []):
                    if obj.type != 'star':
                        if not hasattr(obj, 'system_q') or not hasattr(obj, 'system_r'):
                            # Find unblocked position for this object
                            max_attempts = 50
                            placed = False
                            for _ in range(max_attempts):
                                q = random.randint(0, hex_grid.cols - 1)
                                r = random.randint(0, hex_grid.rows - 1)
                                blocked, _ = is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid)
                                # Also check if another object is already there
                                occupied = any(o != obj and hasattr(o, 'system_q') and o.system_q == q and hasattr(o, 'system_r') and o.system_r == r 
                                             for o in systems.get(current_system, []))
                                if not blocked and not occupied:
                                    obj.system_q = q
                                    obj.system_r = r
                                    placed = True
                                    break
                            if not placed:
                                # Fallback: place at first available hex
                                for q in range(hex_grid.cols):
                                    for r in range(hex_grid.rows):
                                        blocked, _ = is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid)
                                        occupied = any(o != obj and hasattr(o, 'system_q') and o.system_q == q and hasattr(o, 'system_r') and o.system_r == r 
                                                     for o in systems.get(current_system, []))
                                        if not blocked and not occupied:
                                            obj.system_q = q
                                            obj.system_r = r
                                            placed = True
                                            break
                                    if placed:
                                        break
                        px, py = hex_grid.get_hex_center(obj.system_q, obj.system_r)
                        if obj.type == 'starbase':
                            # Use starbase image if available, otherwise fallback to rectangle
                            starbase_img = background_and_star_loader.get_starbase_image()
                            if starbase_img:
                                scaled_starbase = background_and_star_loader.scale_starbase_image(starbase_img, hex_grid.radius)
                                if scaled_starbase:
                                    # Center the image on the hex
                                    img_rect = scaled_starbase.get_rect(center=(int(px), int(py)))
                                    screen.blit(scaled_starbase, img_rect)
                                else:
                                    # Fallback to rectangle if scaling fails
                                    color = (0, 0, 255)
                                    pygame.draw.rect(screen, color, (int(px)-6, int(py)-6, 12, 12))
                            else:
                                # Fallback to rectangle if image not available
                                color = (0, 0, 255)
                                pygame.draw.rect(screen, color, (int(px)-6, int(py)-6, 12, 12))
                        elif obj.type == 'enemy':
                            # Use animated pixel position if available, otherwise static hex position
                            if hasattr(obj, 'anim_px') and hasattr(obj, 'anim_py'):
                                render_px, render_py = obj.anim_px, obj.anim_py
                            else:
                                render_px, render_py = px, py
                            
                            # Use enemy ship image if available, otherwise fallback to triangle
                            enemy_img = background_and_star_loader.get_enemy_ship_image()
                            if enemy_img:
                                scaled_enemy = background_and_star_loader.scale_ship_image(enemy_img, hex_grid.radius)
                                if scaled_enemy:
                                    # Initialize rotation tracking if not exists
                                    if not hasattr(obj, 'current_rotation'):
                                        obj.current_rotation = 0.0
                                    
                                    # Calculate target rotation based on movement direction
                                    # Only update target rotation when movement starts or changes
                                    if not hasattr(obj, 'target_rotation'):
                                        obj.target_rotation = obj.current_rotation
                                    
                                    # Check if this enemy has an AI ship that's moving
                                    enemy_id = id(obj)
                                    if hasattr(player_ship, 'combat_manager') and enemy_id in player_ship.combat_manager.enemy_ships:
                                        enemy_ship = player_ship.combat_manager.enemy_ships[enemy_id]
                                        if enemy_ship.is_moving and enemy_ship.current_destination:
                                            # Enemy is moving - calculate rotation based on current animation position to destination
                                            current_pos = (render_px, render_py)
                                            dest_pos = hex_grid.get_hex_center(enemy_ship.current_destination[0], enemy_ship.current_destination[1])
                                            obj.target_rotation = background_and_star_loader.calculate_movement_angle(current_pos, dest_pos)
                                        elif hasattr(obj, 'prev_render_px') and hasattr(obj, 'prev_render_py'):
                                            # Use previous position to calculate movement direction for smooth transitions
                                            prev_pos = (obj.prev_render_px, obj.prev_render_py)
                                            current_pos = (render_px, render_py)
                                            if prev_pos != current_pos:  # Only rotate if actually moved
                                                # Calculate movement direction from actual position change
                                                import math
                                                distance_moved = math.hypot(current_pos[0] - prev_pos[0], current_pos[1] - prev_pos[1])
                                                if distance_moved > 1.0:  # Reduce threshold for more responsive rotation
                                                    obj.target_rotation = background_and_star_loader.calculate_movement_angle(prev_pos, current_pos)
                                    else:
                                        # Fallback: if no AI ship found, use position-based rotation
                                        if hasattr(obj, 'prev_render_px') and hasattr(obj, 'prev_render_py'):
                                            prev_pos = (obj.prev_render_px, obj.prev_render_py)
                                            current_pos = (render_px, render_py)
                                            if prev_pos != current_pos:
                                                import math
                                                distance_moved = math.hypot(current_pos[0] - prev_pos[0], current_pos[1] - prev_pos[1])
                                                if distance_moved > 1.0:
                                                    obj.target_rotation = background_and_star_loader.calculate_movement_angle(prev_pos, current_pos)
                                    
                                    target_rotation = obj.target_rotation
                                    
                                    # Smoothly interpolate to target rotation
                                    rotation_speed = 900.0  # degrees per second (fast, agile enemy rotation)
                                    obj.current_rotation = background_and_star_loader.interpolate_rotation(
                                        obj.current_rotation, 
                                        target_rotation, 
                                        rotation_speed, 
                                        delta_time
                                    )
                                    
                                    # Store current position for next frame
                                    obj.prev_render_px = render_px
                                    obj.prev_render_py = render_py
                                    
                                    # Apply rotation
                                    rotated_enemy = background_and_star_loader.rotate_ship_image(scaled_enemy, obj.current_rotation)
                                    img_rect = rotated_enemy.get_rect(center=(int(render_px), int(render_py)))
                                    screen.blit(rotated_enemy, img_rect)
                                else:
                                    # Fallback to triangle if scaling fails
                                    color = (255, 0, 0)
                                    pygame.draw.polygon(screen, color, [
                                        (int(render_px), int(render_py)-8),
                                        (int(render_px)-6, int(render_py)+4),
                                        (int(render_px)+6, int(render_py)+4)
                                    ])
                            else:
                                # Fallback to triangle if image not available
                                color = (255, 0, 0)
                                pygame.draw.polygon(screen, color, [
                                    (int(render_px), int(render_py)-8),
                                    (int(render_px)-6, int(render_py)+4),
                                    (int(render_px)+6, int(render_py)+4)
                                ])
                        elif obj.type == 'anomaly':
                            color = (255, 0, 255)
                            pygame.draw.circle(screen, color, (int(px), int(py)), 5)
                        elif obj.type == 'player':
                            # Draw player ship at appropriate position using image if available
                            player_img = background_and_star_loader.get_player_ship_image()
                            if player_img:
                                scaled_player = background_and_star_loader.scale_ship_image(player_img, hex_grid.radius)
                                if scaled_player:
                                    # Initialize rotation tracking if not exists
                                    if not hasattr(obj, 'current_rotation'):
                                        obj.current_rotation = 0.0
                                    
                                    # Calculate target rotation based on movement direction
                                    # Only update target rotation when movement starts or changes
                                    if not hasattr(obj, 'target_rotation'):
                                        obj.target_rotation = obj.current_rotation
                                    
                                    if (game_state.orbital.player_orbiting_planet or system_ship_moving) and system_ship_anim_x is not None and system_ship_anim_y is not None:
                                        # Ship is animated - calculate target rotation
                                        if system_ship_moving and system_dest_q is not None and system_dest_r is not None:
                                            # Moving to destination - only update target rotation when destination changes
                                            if not hasattr(obj, 'last_system_dest_q') or obj.last_system_dest_q != system_dest_q or obj.last_system_dest_r != system_dest_r:
                                                current_pos = (system_ship_anim_x, system_ship_anim_y)
                                                dest_pos = hex_grid.get_hex_center(system_dest_q, system_dest_r)
                                                obj.target_rotation = background_and_star_loader.calculate_movement_angle(current_pos, dest_pos)
                                                obj.last_system_dest_q = system_dest_q
                                                obj.last_system_dest_r = system_dest_r
                                        elif game_state.orbital.player_orbiting_planet:
                                            # Orbiting - calculate rotation based on orbital movement (continuous for smooth orbital rotation)
                                            # Use previous position to calculate movement direction
                                            if hasattr(obj, 'prev_anim_x') and hasattr(obj, 'prev_anim_y'):
                                                prev_pos = (obj.prev_anim_x, obj.prev_anim_y)
                                                current_pos = (system_ship_anim_x, system_ship_anim_y)
                                                obj.target_rotation = background_and_star_loader.calculate_movement_angle(prev_pos, current_pos)
                                        
                                        # Store previous position for next frame's orbital rotation
                                        obj.prev_anim_x = system_ship_anim_x
                                        obj.prev_anim_y = system_ship_anim_y
                                    
                                    target_rotation = obj.target_rotation
                                    
                                    # Smoothly interpolate to target rotation
                                    rotation_speed = 720.0  # degrees per second
                                    obj.current_rotation = background_and_star_loader.interpolate_rotation(
                                        obj.current_rotation, 
                                        target_rotation, 
                                        rotation_speed, 
                                        delta_time
                                    )
                                    
                                    # Apply rotation
                                    rotated_player = background_and_star_loader.rotate_ship_image(scaled_player, obj.current_rotation)
                                    
                                    if (game_state.orbital.player_orbiting_planet or system_ship_moving) and system_ship_anim_x is not None and system_ship_anim_y is not None:
                                        # Use animated position
                                        img_rect = rotated_player.get_rect(center=(int(system_ship_anim_x), int(system_ship_anim_y)))
                                        screen.blit(rotated_player, img_rect)
                                    else:
                                        # Use static position
                                        img_rect = rotated_player.get_rect(center=(int(px), int(py)))
                                        screen.blit(rotated_player, img_rect)
                                else:
                                    # Fallback to circle if scaling fails
                                    color = (0, 255, 255)
                                    if (game_state.orbital.player_orbiting_planet or system_ship_moving) and system_ship_anim_x is not None and system_ship_anim_y is not None:
                                        pygame.draw.circle(screen, color, (int(system_ship_anim_x), int(system_ship_anim_y)), 8)
                                    else:
                                        pygame.draw.circle(screen, color, (int(px), int(py)), 8)
                            else:
                                # Fallback to circle if image not available
                                color = (0, 255, 255)
                                if (game_state.orbital.player_orbiting_planet or system_ship_moving) and system_ship_anim_x is not None and system_ship_anim_y is not None:
                                    pygame.draw.circle(screen, color, (int(system_ship_anim_x), int(system_ship_anim_y)), 8)
                                else:
                                    pygame.draw.circle(screen, color, (int(px), int(py)), 8)

        # Draw player ship
        if game_state.map_mode == 'sector':
            # Use player ship image if available, otherwise fallback to circle
            player_img = background_and_star_loader.get_player_ship_image()
            if player_img:
                scaled_player = background_and_star_loader.scale_ship_image(player_img, hex_grid.radius)
                if scaled_player:
                    # Initialize rotation tracking if not exists
                    if not hasattr(game_state.animation, 'player_current_rotation'):
                        game_state.animation.player_current_rotation = 0.0
                    
                    # Calculate target rotation based on movement direction
                    # Only calculate new target rotation when movement starts or changes, not during movement
                    if not hasattr(game_state.animation, 'player_target_rotation'):
                        game_state.animation.player_target_rotation = game_state.animation.player_current_rotation
                    
                    # Update target rotation only when destination changes
                    if game_state.animation.ship_moving and game_state.animation.dest_q is not None and game_state.animation.dest_r is not None:
                        # Calculate target rotation toward destination
                        current_pos = (game_state.animation.ship_anim_x, game_state.animation.ship_anim_y)
                        dest_pos = hex_grid.get_hex_center(game_state.animation.dest_q, game_state.animation.dest_r)
                        new_target_rotation = background_and_star_loader.calculate_movement_angle(current_pos, dest_pos)
                        
                        # Only update target if it's significantly different (avoid micro-adjustments during movement)
                        if not hasattr(game_state.animation, 'last_dest_q') or game_state.animation.last_dest_q != game_state.animation.dest_q or game_state.animation.last_dest_r != game_state.animation.dest_r:
                            game_state.animation.player_target_rotation = new_target_rotation
                            game_state.animation.last_dest_q = game_state.animation.dest_q
                            game_state.animation.last_dest_r = game_state.animation.dest_r
                    
                    target_rotation = game_state.animation.player_target_rotation
                    
                    # Smoothly interpolate to target rotation
                    rotation_speed = 720.0  # degrees per second (full rotation in 0.5 seconds)
                    game_state.animation.player_current_rotation = background_and_star_loader.interpolate_rotation(
                        game_state.animation.player_current_rotation, 
                        target_rotation, 
                        rotation_speed, 
                        delta_time
                    )
                    
                    # Apply rotation
                    rotated_player = background_and_star_loader.rotate_ship_image(scaled_player, game_state.animation.player_current_rotation)
                    img_rect = rotated_player.get_rect(center=(int(game_state.animation.ship_anim_x), int(game_state.animation.ship_anim_y)))
                    screen.blit(rotated_player, img_rect)
                else:
                    # Fallback to circle if scaling fails
                    pygame.draw.circle(
                        screen, (0, 255, 255), (int(game_state.animation.ship_anim_x), int(game_state.animation.ship_anim_y)), 8
                    )
            else:
                # Fallback to circle if image not available
                pygame.draw.circle(
                    screen, (0, 255, 255), (int(game_state.animation.ship_anim_x), int(game_state.animation.ship_anim_y)), 8
                )
        else:
            # In system mode, remove the separate player_in_system drawing block, as the above already draws the player from system objects
            pass # No player drawing in system mode


        # Right-side Event Log Panel
        right_event_rect = pygame.Rect(event_log_x, event_log_y, event_log_width, event_log_height)
        pygame.draw.rect(screen, COLOR_EVENT_LOG, right_event_rect)
        # Add border to distinguish from screen edge
        pygame.draw.rect(screen, COLOR_EVENT_LOG_BORDER, right_event_rect, 2)
        event_label = label_font.render('Event Log', True, COLOR_TEXT)
        screen.blit(event_label, (event_log_x + 20, event_log_y + 20))
        
        # Popup Dock Area (right of event log)
        popup_dock_x = event_log_x + event_log_width
        popup_dock_rect = pygame.Rect(popup_dock_x, STATUS_HEIGHT, ENEMY_SCAN_WIDTH, HEIGHT - STATUS_HEIGHT)
        pygame.draw.rect(screen, (25, 25, 40), popup_dock_rect)  # Darker background for popup area
        pygame.draw.rect(screen, COLOR_EVENT_LOG_BORDER, popup_dock_rect, 2)
        dock_label = label_font.render('Scan Results', True, COLOR_TEXT)
        screen.blit(dock_label, (popup_dock_x + 20, STATUS_HEIGHT + 20))
        # Draw event log lines with text wrapping
        log_font = small_font  # Use custom small font
        log_area_width = event_log_width - 40  # Account for padding
        y_offset = event_log_y + 50  # Account for Event Log label
        line_height = 20  # Tighter line spacing
        
        # Process and render each log entry with wrapping
        rendered_lines = 0
        for line in game_state.ui.event_log[-EVENT_LOG_MAX_LINES:]:
            if rendered_lines >= EVENT_LOG_MAX_LINES:
                break
                
            wrapped_lines = wrap_text(line, log_area_width, log_font)
            for wrapped_line in wrapped_lines:
                if rendered_lines >= EVENT_LOG_MAX_LINES:
                    break
                text_surface = log_font.render(wrapped_line, True, COLOR_TEXT)
                screen.blit(text_surface, (event_log_x + 20, y_offset + rendered_lines * line_height))
                rendered_lines += 1

        # Image Display Panel (bottom left - formerly event log)
        image_rect = pygame.Rect(0, bottom_pane_y, image_display_width, bottom_pane_height)
        pygame.draw.rect(screen, COLOR_IMAGE_DISPLAY, image_rect)
        image_label = label_font.render('Target Image Display', True, COLOR_TEXT)
        screen.blit(image_label, (20, bottom_pane_y + 20))

        # Control Panel (bottom right)
        control_rect = pygame.Rect(image_display_width, bottom_pane_y, 
                                    control_panel_width, bottom_pane_height)
        pygame.draw.rect(screen, COLOR_CONTROL_PANEL, control_rect)
        control_label = label_font.render('Control Panel', True, COLOR_TEXT)
        screen.blit(control_label, (image_display_width + 20, 
                                     bottom_pane_y + 20))

        # Draw border around button area within control panel
        button_area_padding = 10
        button_area_x = image_display_width + 30
        button_area_y = bottom_pane_y + CONTROL_PANEL_LABEL_SPACER - 10
        button_area_width = control_panel_width - 40
        button_area_height = bottom_pane_height - CONTROL_PANEL_LABEL_SPACER
        button_area_rect = pygame.Rect(button_area_x, button_area_y, button_area_width, button_area_height)
        pygame.draw.rect(screen, COLOR_BUTTON_AREA_BORDER, button_area_rect, 2)
        
        # Draw button panel on top of control panel
        button_rects, toggle_btn_rect = draw_button_panel(
            screen,
            image_display_width,
            bottom_pane_y,
            BUTTON_W,
            BUTTON_H,
            BUTTON_GAP,
            font,
            BUTTON_COLOR,
            COLOR_TEXT,
            game_state.map_mode,
            TOGGLE_BTN_W,
            TOGGLE_BTN_H,
            TOGGLE_BTN_Y
        )
        # Toggle button is available

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle button events first
            if button_rects and toggle_btn_rect:
                (game_state.ui.button_pressed,
                 game_state.ui.toggle_btn_pressed,
                 clicked_index,
                 toggle_clicked) = handle_button_events(
                    event, button_rects, toggle_btn_rect, game_state.ui.button_pressed,
                    game_state.ui.toggle_btn_pressed
                )
                if clicked_index is not None:
                    label = button_labels[clicked_index] if clicked_index < len(button_labels) else str(clicked_index)
                    print(f"[DEBUG] Button {clicked_index} clicked: {label}")
                    # --- Use label-based action selection ---
                    if label == "Move":
                        add_event_log("Move mode: Click on a hex to navigate")
                    elif label == "Torpedo":
                        print(f"[DEBUG] Entered Torpedo button handler: map_mode={game_state.map_mode}, selected_enemy={game_state.combat.selected_enemy}")
                        
                        # Check torpedo availability first
                        if not player_ship.has_torpedoes():
                            add_event_log("*** NO TORPEDOES REMAINING ***")
                            add_event_log("Dock at a starbase to replenish torpedo supplies!")
                            sound_manager.play_sound('error')  # Play error sound
                            continue  # Skip the rest of the torpedo logic
                        
                        # Check if torpedoes are on cooldown
                        if player_ship.torpedo_system.is_on_cooldown():
                            cooldown_time = (player_ship.torpedo_system._last_fired_time + player_ship.torpedo_system.cooldown_seconds) - time.time()
                            add_event_log(f"Torpedoes reloading - {cooldown_time:.1f}s remaining")
                            sound_manager.play_sound('error')  # Play error sound if available
                            continue  # Skip the rest of the torpedo logic
                        
                        # Fire torpedoes at selected enemy (only works in system mode)
                        if game_state.map_mode == 'system':
                            print("[DEBUG] In system mode")
                            if game_state.combat.selected_enemy is not None:
                                print(f"[DEBUG] game_state.combat.selected_enemy is not None: {game_state.combat.selected_enemy}")
                                player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                                print(f"[DEBUG] player_obj found: {player_obj}")
                                
                                if player_obj is not None and hasattr(player_obj, 'system_q') and hasattr(game_state.combat.selected_enemy, 'system_q'):
                                    dx = game_state.combat.selected_enemy.system_q - player_obj.system_q
                                    dy = game_state.combat.selected_enemy.system_r - player_obj.system_r
                                    distance = math.hypot(dx, dy)
                                    
                                    # Get start and target positions for animation
                                    # Use animated position (orbital or movement) if available, otherwise use static position
                                    if system_ship_anim_x is not None and system_ship_anim_y is not None:
                                        start_pos = (system_ship_anim_x, system_ship_anim_y)
                                    else:
                                        start_pos = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                                    target_pos = get_enemy_current_position(game_state.combat.selected_enemy, hex_grid)
                                    
                                    # Fire torpedo using weapon animation manager
                                    target_hex_pos = (game_state.combat.selected_enemy.system_q, game_state.combat.selected_enemy.system_r)
                                    result = game_state.weapon_animation_manager.fire_torpedo(
                                        game_state.combat.selected_enemy, distance, start_pos, target_pos, target_hex_pos
                                    )
                                    
                                    if result['success']:
                                        add_event_log("Torpedo launched!")
                                        # Check for low torpedo warning
                                        if player_ship.torpedo_count <= 3 and player_ship.torpedo_count > 0:
                                            add_event_log(f"*** LOW TORPEDO SUPPLY: {player_ship.torpedo_count} remaining ***")
                                        elif player_ship.torpedo_count == 0:
                                            add_event_log("*** LAST TORPEDO EXPENDED ***")
                                    else:
                                        add_event_log(f"Torpedo launch failed: {result.get('reason', 'Unknown error')}")
                                else:
                                    add_event_log("Cannot determine target position")
                            else:
                                add_event_log("No enemy target selected. Right-click an enemy to target it first.")
                        else:
                            add_event_log("Torpedoes can only be fired in system view")
                    elif label == "Scan":
                        print("Scan initiated!")
                        # Play scanner sound effect
                        sound_manager.play_sound('scanner')
                        if game_state.map_mode == 'sector':
                            game_state.scan.sector_scan_active = True
                            add_event_log("Long-range sensors activated. All systems revealed.")
                            print("Sector scan active. All systems revealed.")
                        elif game_state.map_mode == 'system':
                            # Check if we have targeted enemies to scan
                            if game_state.combat.targeted_enemies:
                                print(f"[DEBUG] Scanning {len(game_state.combat.targeted_enemies)} targeted enemies")
                                # Create/show popups for all targeted enemies
                                new_popups = 0
                                for enemy_id, enemy_obj in game_state.combat.targeted_enemies.items():
                                    print(f"[DEBUG] Processing enemy {enemy_id}")
                                    if enemy_id not in game_state.scan.enemy_popups:
                                        # Create new popup for this enemy
                                        popup_info = create_enemy_popup(enemy_id, enemy_obj)
                                        game_state.scan.enemy_popups[enemy_id] = popup_info
                                        new_popups += 1
                                        print(f"[DEBUG] Created popup for enemy {enemy_id}")
                                    # Show the popup
                                    game_state.scan.enemy_popups[enemy_id]['visible'] = True
                                    print(f"[DEBUG] Popup {enemy_id} visible: {game_state.scan.enemy_popups[enemy_id]['visible']}")
                                
                                if new_popups > 0:
                                    add_event_log(f"Scanning {new_popups} targeted enemies - detailed sensor data displayed")
                                else:
                                    add_event_log(f"Updating sensor data for {len(game_state.combat.targeted_enemies)} targeted enemies")
                            else:
                                # No targeted enemies, perform system scan as before
                                if current_system not in game_state.scan.scanned_systems:
                                    game_state.scan.scanned_systems.add(current_system)
                                    add_event_log("System scan complete. No enemies targeted - right-click enemies to target them for detailed scans.")
                                    
                                    # Only generate/modify system objects if not already scanned
                                    # Diagnostic logging for scan
                                    logging.info(f"[SCAN] current_system: {current_system}")
                                    for obj_type, coords_set in lazy_object_coords.items():
                                        logging.info(f"[SCAN] {obj_type}: current_system in set? {current_system in coords_set}")
                                        logging.info(f"[SCAN] {obj_type} set: {coords_set}")
                                    
                                    # Store all objects (including star) for this system for persistence (as dicts)
                                    system_objs = generate_system_objects(
                                        current_system[0],
                                        current_system[1],
                                        lazy_object_coords,
                                        star_coords=star_coords,
                                        planet_orbits=planet_orbits,
                                        grid_size=hex_grid.cols
                                    )
                                    
                                    # Preserve existing player ship position if it exists
                                    existing_player = None
                                    if current_system in systems:
                                        existing_player = next((obj for obj in systems[current_system] if obj.type == 'player'), None)
                                    
                                    # Assign random system positions to non-player objects
                                    for obj in system_objs:
                                        if obj.type == 'player' and existing_player:
                                            # Preserve existing player position
                                            obj.system_q = existing_player.system_q
                                            obj.system_r = existing_player.system_r
                                        else:
                                            # Assign random position to other objects
                                            obj.system_q = random.randint(0, hex_grid.cols - 1)
                                            obj.system_r = random.randint(0, hex_grid.rows - 1)
                                    
                                    # Fix planet visibility: ensure planets in this hex are added to planet_orbits
                                    # Note: planets are now stored in planet_orbits, not lazy_object_coords
                                    planets_in_hex = [orbit['planet'] for orbit in planet_orbits if orbit['star'] == current_system]
                                    for planet_coord in planets_in_hex:
                                        # Check if this planet is already in planet_orbits (it should be)
                                        existing_orbit = next((orbit for orbit in planet_orbits if orbit['planet'] == planet_coord), None)
                                        if not existing_orbit:
                                            # This should not happen with the new system, but keep as fallback
                                            new_orbit = {
                                                'star': current_system,
                                                'planet': planet_coord,
                                                'hex_radius': random.randint(8, 15),  # Minimum 4 hex from star outer bounds
                                                'angle': random.uniform(0, 2 * math.pi),
                                                'speed': random.uniform(0.02, 0.1)  # Speed in radians per second
                                            }
                                            planet_orbits.append(new_orbit)
                                            # Add to animation state
                                            planet_anim_state[(current_system, planet_coord)] = new_orbit['angle']
                                            logging.info(f"[SCAN] Added missing planet {planet_coord} to orbit around star {current_system}")
                                    
                                    # Only update systems if this is a first-time scan
                                    systems[current_system] = system_objs
                                    game_state.system_object_states[current_system] = [
                                        {
                                            'type': obj.type,
                                            'q': obj.q,
                                            'r': obj.r,
                                            'system_q': obj.system_q,
                                            'system_r': obj.system_r,
                                            'props': obj.props
                                        } for obj in system_objs
                                    ]
                                    
                                    # --- Ensure player object exists and is placed at a random, unoccupied hex (after scan) ---
                                    # Only for first-time scans
                                    player_obj = next((obj for obj in systems[current_system] if obj.type == 'player'), None)
                                    if player_obj is None:
                                        occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                                                       for obj in systems[current_system] if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))
                                        max_attempts = 100
                                        for _ in range(max_attempts):
                                            rand_q = random.randint(0, hex_grid.cols - 1)
                                            rand_r = random.randint(0, hex_grid.rows - 1)
                                            # Check both occupied set and blocked hexes
                                            blocked, _ = is_hex_blocked(rand_q, rand_r, current_system, systems, planet_orbits, hex_grid)
                                            if (rand_q, rand_r) not in occupied and not blocked:
                                                player_obj = MapObject('player', current_system[0], current_system[1])
                                                player_obj.system_q = rand_q
                                                player_obj.system_r = rand_r
                                                systems[current_system].append(player_obj)
                                                break
                                        else:
                                            # Find any unblocked hex as fallback
                                            for attempt_q in range(hex_grid.cols):
                                                for attempt_r in range(hex_grid.rows):
                                                    blocked, _ = is_hex_blocked(attempt_q, attempt_r, current_system, systems, planet_orbits, hex_grid)
                                                    if not blocked:
                                                        player_obj = MapObject('player', current_system[0], current_system[1])
                                                        player_obj.system_q = attempt_q
                                                        player_obj.system_r = attempt_r
                                                        systems[current_system].append(player_obj)
                                                        break
                                                if player_obj:
                                                    break
                                else:
                                    # System already scanned, just inform user
                                    add_event_log("System already scanned. Right-click enemies to target them for detailed scans.")
                    elif label == "Fire":
                        print(f"[DEBUG] Entered Fire button handler: map_mode={game_state.map_mode}, selected_enemy={game_state.combat.selected_enemy}")
                        
                        # Check if phasers are on cooldown first
                        if player_ship.phaser_system.is_on_cooldown():
                            cooldown_time = (player_ship.phaser_system._last_fired_time + player_ship.phaser_system.cooldown_seconds) - time.time()
                            add_event_log(f"Phasers recharging - {cooldown_time:.1f}s remaining")
                            sound_manager.play_sound('error')  # Play error sound if available
                            continue  # Skip the rest of the fire logic
                        
                        # Fire phasers at selected enemy (only works in system mode)
                        if game_state.map_mode == 'system':
                            print("[DEBUG] In system mode")
                            if game_state.combat.selected_enemy is not None:
                                print(f"[DEBUG] game_state.combat.selected_enemy is not None: {game_state.combat.selected_enemy}")
                                player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                                print(f"[DEBUG] player_obj found: {player_obj}")
                                if player_obj is None:
                                    print("[DEBUG] No player object found in current system! Adding player object.")
                                    occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                                                   for obj in systems[current_system] if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))
                                    # Try random positions until an unoccupied one is found
                                    max_attempts = 100
                                    for _ in range(max_attempts):
                                        rand_q = random.randint(0, hex_grid.cols - 1)
                                        rand_r = random.randint(0, hex_grid.rows - 1)
                                        if (rand_q, rand_r) not in occupied:
                                            player_obj = MapObject('player', current_system[0], current_system[1])
                                            player_obj.system_q = rand_q
                                            player_obj.system_r = rand_r
                                            systems[current_system].append(player_obj)
                                            print(f"[DEBUG] Player object added at ({rand_q}, {rand_r})")
                                            break
                                    else:
                                        # Fallback: place at (0, 0)
                                        player_obj = MapObject('player', current_system[0], current_system[1])
                                        player_obj.system_q = 0
                                        player_obj.system_r = 0
                                        systems[current_system].append(player_obj)
                                        print("[DEBUG] Player object added at fallback (0, 0)")
                                # Continue with phaser logic as before
                                if player_obj is not None and hasattr(player_obj, 'system_q') and hasattr(game_state.combat.selected_enemy, 'system_q'):
                                    dx = game_state.combat.selected_enemy.system_q - player_obj.system_q
                                    dy = game_state.combat.selected_enemy.system_r - player_obj.system_r
                                    distance = math.hypot(dx, dy)
                                    if distance <= phaser_range:
                                        # Fire phaser using weapon animation manager
                                        result = game_state.weapon_animation_manager.fire_phaser(
                                            game_state.combat.selected_enemy, distance
                                        )
                                        
                                        if result['success']:
                                            # Play phaser sequence: shot followed by explosion
                                            sound_manager.play_phaser_sequence()
                                            add_event_log("Phaser fired!")
                                        else:
                                            add_event_log(f"Phaser fire failed: {result.get('reason', 'Unknown error')}")
                                    else:
                                        add_event_log(f"Target out of range! Max range: {phaser_range} hexes")
                                else:
                                    add_event_log("No target selected! Right-click an enemy ship.")
                            else:
                                add_event_log("No target selected! Right-click an enemy ship.")
                        else:
                            add_event_log("Weapons offline in sector view. Enter a system first.")

                if toggle_clicked:
                    print("Toggle button clicked")
                    # Play keypress sound effect
                    sound_manager.play_sound('keypress')
                    new_mode = 'system' if game_state.map_mode == 'sector' else 'sector'
                    add_event_log(f"Switched to {new_mode} view")
                    game_state.map_mode = new_mode

            # Handle ship status display clicks first
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Check if click is on ship status display (power allocation)
                if ship_status_display.handle_click((mx, my), player_ship):
                    continue  # Power allocation changed, skip other click handling
            
            # Then handle map click events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if map_rect.collidepoint(mx, my) and game_state.map_mode == 'sector':
                    q, r = hex_grid.pixel_to_hex(mx, my)
                    if q is not None and r is not None:
                        # Determine starting position for trajectory calculation
                        if game_state.animation.ship_moving:
                            # Ship is mid-flight - use current animated position as starting point
                            start_hex_q, start_hex_r = hex_grid.pixel_to_hex(game_state.animation.ship_anim_x, game_state.animation.ship_anim_y)
                            if start_hex_q is None or start_hex_r is None:
                                # Fallback to current ship position if conversion fails
                                start_hex_q, start_hex_r = ship_q, ship_r
                            log_debug(f"[REDIRECT] Ship redirecting mid-flight from animated position ({start_hex_q}, {start_hex_r}) to ({q}, {r})")
                        else:
                            # Ship is stationary - use actual ship position
                            start_hex_q, start_hex_r = ship_q, ship_r
                        
                        # Calculate distance for warp travel from current position
                        dx = abs(q - start_hex_q)
                        dy = abs(r - start_hex_r)
                        distance = max(dx, dy)  # Hex distance approximation
                        
                        # Calculate energy cost: 20 for initiation + 10 per sector
                        # Note: For mid-flight changes, we don't charge initiation cost again
                        if game_state.animation.ship_moving:
                            energy_cost = distance * constants.WARP_ENERGY_COST  # No initiation cost for redirects
                            action_msg = "Changing course"
                        else:
                            energy_cost = constants.WARP_INITIATION_COST + (distance * constants.WARP_ENERGY_COST)
                            action_msg = "Setting course"
                        
                        # Calculate dynamic energy cost based on engine power
                        dynamic_energy_cost = player_ship.get_movement_energy_cost(energy_cost)
                        
                        # Check if player has enough energy
                        if player_ship.warp_core_energy >= dynamic_energy_cost:
                            # Calculate dynamic movement duration based on engine power
                            base_duration = 2000  # 2 seconds base warp time
                            movement_duration = player_ship.get_movement_duration(base_duration)
                            
                            game_state.animation.dest_q, game_state.animation.dest_r = q, r
                            game_state.animation.ship_moving = True
                            game_state.animation.move_start_time = pygame.time.get_ticks()
                            game_state.animation.move_duration_ms = movement_duration  # Set dynamic duration
                            
                            # Set trajectory start position (current animated position for mid-flight changes)
                            trajectory_start_x, trajectory_start_y = game_state.animation.ship_anim_x, game_state.animation.ship_anim_y
                            end_x, end_y = hex_grid.get_hex_center(game_state.animation.dest_q, game_state.animation.dest_r)
                            
                            # Play warp sound for dynamic duration
                            sound_manager.play_movement_sound('warp', movement_duration)
                            
                            # Update energy cost in event log
                            engine_power = player_ship.power_allocation.get('engines', 5)
                            efficiency = player_ship.get_engine_efficiency()
                            add_event_log(f"{action_msg} for sector ({q}, {r}) - Engine Power: {engine_power} - Duration: {movement_duration/1000:.1f}s")
                            add_event_log(f"Energy cost: {dynamic_energy_cost} - Engine efficiency: {efficiency:.1f}x")
                            print(f"Ship moving to hex ({q}, {r}) - Duration: {movement_duration}ms - Energy cost: {dynamic_energy_cost}")
                        else:
                            add_event_log(f"Insufficient energy! Need {energy_cost}, have {player_ship.warp_core_energy}")
                            sound_manager.play_sound('error')  # Play error sound if available
                elif map_rect.collidepoint(mx, my) and game_state.map_mode == 'system' and current_system in game_state.scan.scanned_systems:
                    # System map navigation
                    # Find player object in current system
                    player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                    if player_obj is not None:
                        q, r = hex_grid.pixel_to_hex(mx, my)
                        if q is not None and r is not None:
                            # Check if destination is blocked
                            blocked, block_type = is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid)
                            if blocked:
                                if block_type == 'planet':
                                    # Show orbital dialog for planets
                                    wants_orbit = show_orbit_dialog(screen, font)
                                    if wants_orbit:
                                        # Find the planet at this location
                                        planet_found = False
                                        planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
                                        for orbit in planets_in_system:
                                            # Get star position to calculate planet position
                                            star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
                                            if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
                                                star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
                                                hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
                                                orbit_radius_px = orbit['hex_radius'] * hex_size
                                                key = (orbit['star'], orbit['planet'])
                                                angle = planet_anim_state.get(key, orbit['angle'])
                                                planet_px = star_px + orbit_radius_px * math.cos(angle)
                                                planet_py = star_py + orbit_radius_px * math.sin(angle)
                                                
                                                # Check if this planet is at the clicked location
                                                planet_q, planet_r = hex_grid.pixel_to_hex(planet_px, planet_py)
                                                if planet_q is not None and planet_r is not None:
                                                    planet_hexes = get_planet_hexes(planet_q, planet_r)
                                                    if (q, r) in planet_hexes:
                                                        # Check if we're already at this location
                                                        current_player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                                                        if current_player_obj and current_player_obj.system_q == q and current_player_obj.system_r == r:
                                                            # Already at planet location - start orbiting immediately
                                                            game_state.orbital.player_orbiting_planet = True
                                                            game_state.orbital.player_orbit_center = (planet_px, planet_py)
                                                            player_orbit_key = key
                                                            game_state.orbital.orbital_angle = 0.0
                                                            add_event_log(f"Entering orbit around planet at ({q}, {r})")
                                                        else:
                                                            # Need to move to planet first, then orbit
                                                            # Calculate movement cost and check energy
                                                            if current_player_obj:
                                                                dx = abs(q - current_player_obj.system_q)
                                                                dy = abs(r - current_player_obj.system_r)
                                                                distance = max(dx, dy)
                                                                energy_cost = distance * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
                                                                
                                                                if player_ship.warp_core_energy >= energy_cost:
                                                                    # Store pending orbit info
                                                                    pending_orbit_center = (planet_px, planet_py)
                                                                    pending_orbit_key = key
                                                                    
                                                                    # Start movement to planet
                                                                    system_dest_q, system_dest_r = q, r
                                                                    system_ship_moving = True
                                                                    system_move_start_time = pygame.time.get_ticks()
                                                                    
                                                                    # Set movement trajectory
                                                                    if system_ship_anim_x is not None and system_ship_anim_y is not None:
                                                                        system_trajectory_start_x, system_trajectory_start_y = system_ship_anim_x, system_ship_anim_y
                                                                    else:
                                                                        start_pos_x, start_pos_y = hex_grid.get_hex_center(current_player_obj.system_q, current_player_obj.system_r)
                                                                        system_ship_anim_x, system_ship_anim_y = start_pos_x, start_pos_y
                                                                        system_trajectory_start_x, system_trajectory_start_y = start_pos_x, start_pos_y
                                                                    
                                                                    # Stop any current orbit
                                                                    game_state.orbital.player_orbiting_planet = False
                                                                    game_state.orbital.player_orbit_center = None
                                                                    
                                                                    add_event_log(f"Moving to planet at ({q}, {r}) to enter orbit")
                                                                else:
                                                                    add_event_log(f"Insufficient energy to reach planet at ({q}, {r}). Need {energy_cost}, have {player_ship.warp_core_energy}")
                                                            else:
                                                                add_event_log("Cannot find player position for orbital movement")
                                                        
                                                        planet_found = True
                                                        break
                                        
                                        if not planet_found:
                                            add_event_log(f"Cannot find planet at ({q}, {r})")
                                    else:
                                        add_event_log(f"Cannot move to ({q}, {r}) - blocked by {block_type}!")
                                else:
                                    add_event_log(f"Cannot move to ({q}, {r}) - blocked by {block_type}!")
                            else:
                                # Exit orbit mode if player was orbiting a planet
                                if game_state.orbital.player_orbiting_planet:
                                    game_state.orbital.player_orbiting_planet = False
                                    game_state.orbital.player_orbit_center = None
                                    player_orbit_key = None
                                    add_event_log("Breaking orbit")
                                
                                # Determine starting position for trajectory calculation
                                if system_ship_moving:
                                    # Ship is mid-flight - use current animated position as starting point
                                    start_hex_q, start_hex_r = hex_grid.pixel_to_hex(system_ship_anim_x, system_ship_anim_y)
                                    if start_hex_q is None or start_hex_r is None:
                                        # Fallback to player object position if conversion fails
                                        start_hex_q, start_hex_r = player_obj.system_q, player_obj.system_r
                                    log_debug(f"[SYSTEM_REDIRECT] Ship redirecting mid-flight from animated position ({start_hex_q}, {start_hex_r}) to ({q}, {r})")
                                    action_msg = "Changing course"
                                else:
                                    # Ship is stationary - use actual player object position
                                    start_hex_q, start_hex_r = player_obj.system_q, player_obj.system_r
                                    action_msg = "Setting course"
                                
                                # Calculate distance for impulse movement from current position
                                dx = abs(q - start_hex_q)
                                dy = abs(r - start_hex_r)
                                distance = max(dx, dy)  # Hex distance approximation
                                
                                # Calculate energy cost: 5 per hex for impulse
                                base_energy_cost = distance * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
                                # Calculate dynamic energy cost based on engine power
                                energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                                
                                # Check if player has enough energy
                                if player_ship.warp_core_energy >= energy_cost:
                                    # Calculate dynamic movement duration based on engine power
                                    base_duration = 1000  # 1 second base impulse time
                                    movement_duration = player_ship.get_movement_duration(base_duration)
                                    
                                    system_dest_q, system_dest_r = q, r
                                    system_ship_moving = True
                                    system_move_start_time = pygame.time.get_ticks()
                                    system_move_duration_ms = movement_duration  # Set dynamic duration
                                    
                                    # Set system trajectory start position (current animated position for mid-flight changes)
                                    if system_ship_anim_x is not None and system_ship_anim_y is not None:
                                        # Use current animated position as starting point
                                        system_trajectory_start_x, system_trajectory_start_y = system_ship_anim_x, system_ship_anim_y
                                    else:
                                        # Initialize animated position and trajectory from player object position
                                        start_pos_x, start_pos_y = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                                        system_ship_anim_x, system_ship_anim_y = start_pos_x, start_pos_y
                                        system_trajectory_start_x, system_trajectory_start_y = start_pos_x, start_pos_y
                                    # Play impulse sound for dynamic duration
                                    sound_manager.play_movement_sound('impulse', movement_duration)
                                    
                                    # Update event log with engine power info
                                    engine_power = player_ship.power_allocation.get('engines', 5)
                                    efficiency = player_ship.get_engine_efficiency()
                                    add_event_log(f"{action_msg} for system hex ({q}, {r}) - Engine Power: {engine_power} - Duration: {movement_duration/1000:.1f}s")
                                    add_event_log(f"Energy cost: {energy_cost} - Engine efficiency: {efficiency:.1f}x")
                                    print(f"System ship moving to hex ({q}, {r}) - Duration: {movement_duration}ms - Energy cost: {energy_cost}")
                                else:
                                    add_event_log(f"Insufficient energy! Need {energy_cost}, have {player_ship.warp_core_energy}")
                                    sound_manager.play_sound('error')  # Play error sound if available
            
            # Right-click: target enemy in system mode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
                mx, my = event.pos
                if map_rect.collidepoint(mx, my) and game_state.map_mode == 'system':
                    q, r = hex_grid.pixel_to_hex(mx, my)
                    print(f"[DEBUG] Right-click at pixel=({mx},{my}), hex=({q},{r})")
                    print("[DEBUG] Enemy objects in current system:")
                    for obj in systems.get(current_system, []):
                        if obj.type == 'enemy' and hasattr(obj, 'system_q'):
                            print(f"  Enemy at ({obj.system_q}, {obj.system_r})")
                    if q is not None and r is not None:
                        # Find enemy at this hex
                        found_enemy = None
                        for obj in systems.get(current_system, []):
                            if obj.type == 'enemy' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                                if obj.system_q == q and obj.system_r == r:
                                    found_enemy = obj
                                    break
                        
                        if found_enemy is not None:
                            # Get or assign enemy ID
                            enemy_id = get_enemy_id(found_enemy)
                            
                            # Always update selected_enemy to allow target switching
                            game_state.combat.selected_enemy = found_enemy
                            
                            # Check if this enemy is already in targeted_enemies
                            if enemy_id in game_state.combat.targeted_enemies:
                                add_event_log(f"Switching target to {enemy_id}")
                                print(f"[DEBUG] Switched target to existing enemy {enemy_id}")
                            else:
                                # Add to targeted enemies for the first time
                                game_state.combat.targeted_enemies[enemy_id] = found_enemy
                                add_event_log(f"Target {enemy_id} acquired at ({q}, {r})")
                                print(f"[DEBUG] New enemy {enemy_id} targeted at ({found_enemy.system_q}, {found_enemy.system_r})")
                            
                            # Perform enemy scan and add to scan panel
                            perform_enemy_scan(found_enemy, enemy_id)
                            
                            print(f"[DEBUG] Active target is now enemy {enemy_id}")
                            print(f"[DEBUG] targeted_enemies contains {len(game_state.combat.targeted_enemies)} total enemies")
                        else:
                            add_event_log(f"No enemy at ({q}, {r})")

        # Update ship position (delta time based)
        if game_state.animation.ship_moving and game_state.animation.dest_q is not None and game_state.animation.dest_r is not None:
            now = pygame.time.get_ticks()
            elapsed = now - game_state.animation.move_start_time if game_state.animation.move_start_time is not None else 0
            # Use trajectory start position if available, otherwise fall back to ship hex position
            if trajectory_start_x is not None and trajectory_start_y is not None:
                start_x, start_y = trajectory_start_x, trajectory_start_y
            else:
                start_x, start_y = hex_grid.get_hex_center(ship_q, ship_r)
            end_x, end_y = hex_grid.get_hex_center(game_state.animation.dest_q, game_state.animation.dest_r)
            t = min(elapsed / game_state.animation.move_duration_ms, 1.0)
            game_state.animation.ship_anim_x = start_x + (end_x - start_x) * t
            game_state.animation.ship_anim_y = start_y + (end_y - start_y) * t
            if t >= 1.0:
                # Arrived at destination
                game_state.animation.ship_anim_x, game_state.animation.ship_anim_y = end_x, end_y
                
                # Calculate and consume energy for the warp travel
                dx = abs(game_state.animation.dest_q - ship_q)
                dy = abs(game_state.animation.dest_r - ship_r)
                distance = max(dx, dy)
                base_energy_cost = constants.WARP_INITIATION_COST + (distance * constants.WARP_ENERGY_COST)
                energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                player_ship.consume_energy(energy_cost)
                
                ship_q, ship_r = game_state.animation.dest_q, game_state.animation.dest_r
                game_state.animation.ship_moving = False
                game_state.animation.move_start_time = None
                
                # Stop movement sound when warp completes
                sound_manager.stop_movement_sound()
                trajectory_start_x, trajectory_start_y = None, None  # Reset trajectory tracking
                logging.info(f"[MOVE] Ship arrived at ({ship_q}, {ship_r}), consumed {energy_cost} energy")
                add_event_log(f"Arrived at sector ({ship_q}, {ship_r}) - Energy: {player_ship.warp_core_energy}/{player_ship.max_warp_core_energy}")
                # Check if there's a system here (star or any lazy object, but not individual planets)
                system_here = (
                    (ship_q, ship_r) in star_coords or
                    any((ship_q, ship_r) in coords_set for coords_set in lazy_object_coords.values())
                )
                logging.info(f"[MOVE] Entering coordinate ({ship_q}, {ship_r})")
                if system_here:
                    add_event_log(f"Entered system at ({ship_q}, {ship_r})")
                else:
                    add_event_log(f"Arrived at coordinate ({ship_q}, {ship_r})")
                
                game_state.map_mode = 'system'
                game_state.current_system = (ship_q, ship_r)
                current_system = game_state.current_system
                
                # Clear enemy tracking data when entering new system
                enemy_scan_panel.clear_scans()
                game_state.scan.enemy_popups.clear()
                game_state.combat.targeted_enemies.clear()
                game_state.combat.selected_enemy = None
                add_event_log("Enemy scan data cleared - new system")
                
                # Break orbital state when entering a new system
                if game_state.orbital.player_orbiting_planet:
                    game_state.orbital.player_orbiting_planet = False
                    game_state.orbital.player_orbit_center = None
                    player_orbit_key = None
                    system_ship_anim_x = None
                    system_ship_anim_y = None
                    add_event_log("Breaking orbit - entered new system")
                
                # Store the expected enemy count for later
                enemy_count_expected = lazy_object_coords.get('enemy', []).count(current_system)
                
                # Generate or restore objects for this system
                # Check if we need to regenerate due to missing enemies
                need_regeneration = False
                if current_system in systems:
                    # Check if expected enemies are missing from cached system
                    existing_enemies = [obj for obj in systems[current_system] if obj.type == 'enemy']
                    if enemy_count_expected > 0 and len(existing_enemies) == 0:
                        need_regeneration = True
                        log_debug(f"[WIREFRAME] System {current_system} needs regeneration: expected {enemy_count_expected} enemies but has {len(existing_enemies)}")
                        add_event_log(f"[DEBUG] Regenerating system due to missing enemies")
                
                if current_system not in systems or need_regeneration:
                    # Debug: verify lazy_object_coords is intact
                    enemy_check = lazy_object_coords.get('enemy', []).count(current_system)
                    add_event_log(f"[DEBUG] Before generate: enemy count = {enemy_check}")
                    add_event_log(f"[DEBUG] lazy_object_coords keys: {list(lazy_object_coords.keys())}")
                    log_debug(f"[WIREFRAME] Before generate_system_objects: enemy count = {enemy_check}")
                    log_debug(f"[WIREFRAME] lazy_object_coords keys: {list(lazy_object_coords.keys())}")
                    log_debug(f"[WIREFRAME] lazy_object_coords['enemy'] type: {type(lazy_object_coords.get('enemy', []))}")
                    log_debug(f"[WIREFRAME] lazy_object_coords['enemy'] length: {len(lazy_object_coords.get('enemy', []))}")
                    
                    system_objs = generate_system_objects(
                        current_system[0],
                        current_system[1],
                        lazy_object_coords,
                        star_coords=star_coords,
                        planet_orbits=planet_orbits,
                        grid_size=hex_grid.cols
                    )
                    systems[current_system] = system_objs
                    log_debug(f"[WIREFRAME] generate_system_objects returned {len(system_objs)} objects")
                    game_state.system_object_states[current_system] = [
                        {
                            'type': obj.type,
                            'q': obj.q,
                            'r': obj.r,
                            'system_q': getattr(obj, 'system_q', None),
                            'system_r': getattr(obj, 'system_r', None),
                            'props': obj.props
                        } for obj in system_objs
                    ]
                    if system_objs:
                        logging.info(f"[MOVE] Generated {len(system_objs)} objects for system {current_system}")
                    else:
                        logging.info(f"[MOVE] Generated empty system at {current_system}")
                else:
                    logging.info(f"[MOVE] Using existing objects for system {current_system}")
                # --- Ensure player object exists and is placed at a random, unoccupied hex ---
                player_obj = next((obj for obj in systems[current_system] if obj.type == 'player'), None)
                if player_obj is None:
                    # Find all occupied hexes in system
                    occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                                   for obj in systems[current_system] if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))
                    # Try random positions until an unoccupied one is found
                    max_attempts = 100
                    for _ in range(max_attempts):
                        rand_q = random.randint(0, hex_grid.cols - 1)
                        rand_r = random.randint(0, hex_grid.rows - 1)
                        if (rand_q, rand_r) not in occupied:
                            player_obj = MapObject('player', ship_q, ship_r)
                            player_obj.system_q = rand_q
                            player_obj.system_r = rand_r
                            systems[current_system].append(player_obj)
                            break
                    else:
                        # Fallback: just add at (0,0)
                        player_obj = MapObject('player', ship_q, ship_r)
                        player_obj.system_q = 0
                        player_obj.system_r = 0
                        systems[current_system].append(player_obj)
                else:
                    # If player_obj exists but has no system_q/system_r, assign it
                    if not hasattr(player_obj, 'system_q') or not hasattr(player_obj, 'system_r'):
                        occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                                       for obj in systems[current_system] if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))
                        max_attempts = 100
                        for _ in range(max_attempts):
                            rand_q = random.randint(0, hex_grid.cols - 1)
                            rand_r = random.randint(0, hex_grid.rows - 1)
                            if (rand_q, rand_r) not in occupied:
                                player_obj.system_q = rand_q
                                player_obj.system_r = rand_r
                                break
                        else:
                            player_obj.system_q = 0
                            player_obj.system_r = 0
                
                # Now run the automatic scan to show what's in the system
                add_event_log(f"Auto-scanning system at ({ship_q}, {ship_r})...")
                log_debug(f"[WIREFRAME] Auto-scanning system at ({ship_q}, {ship_r})")
                
                # First check system type
                is_star_system = current_system in star_coords
                has_planets = any(orbit['star'] == current_system for orbit in planet_orbits)
                system_type = "EMPTY"
                if is_star_system and has_planets:
                    system_type = "STAR+PLANET"
                elif is_star_system:
                    system_type = "STAR ONLY"
                
                add_event_log(f"[SYSTEM TYPE] {system_type}")
                add_event_log(f"[DEBUG] Expected enemies from placement: {enemy_count_expected}")
                log_debug(f"[WIREFRAME] System type: {system_type}, Expected enemies: {enemy_count_expected}")
                
                # Show what objects are actually in this system
                system_objects = systems.get(current_system, [])
                log_debug(f"[WIREFRAME] System {current_system} has {len(system_objects)} objects")
                
                # Update weapon animation manager with current system objects
                if game_state.weapon_animation_manager:
                    game_state.weapon_animation_manager.system_objects = system_objects
                
                # Update enemy AI through combat manager (after all system objects are generated)
                delta_time = clock.get_time() / 1000.0  # Convert milliseconds to seconds
                player_ship.combat_manager.update_enemy_ai(delta_time, systems, game_state.current_system, hex_grid, player_ship)
                
                # Show detailed object information
                add_event_log(f"[SCAN] System contains {len(system_objects)} objects:")
                obj_summary = {}
                for obj in system_objects:
                    obj_summary[obj.type] = obj_summary.get(obj.type, 0) + 1
                
                # List each object type and count
                for obj_type, count in sorted(obj_summary.items()):
                    add_event_log(f"  {obj_type}: {count}")
                    log_debug(f"[WIREFRAME] Object count - {obj_type}: {count}")
                
                # Specifically list enemy positions if any
                enemy_objects = [obj for obj in system_objects if obj.type == 'enemy']
                if enemy_objects:
                    add_event_log(f"[ENEMIES] {len(enemy_objects)} enemy ships detected:")
                    log_debug(f"[WIREFRAME] Found {len(enemy_objects)} enemy objects in system")
                    for i, enemy in enumerate(enemy_objects):
                        pos_info = f"({enemy.system_q}, {enemy.system_r})" if hasattr(enemy, 'system_q') else "NO POS"
                        add_event_log(f"  Enemy {i+1} at system pos {pos_info}")
                        log_debug(f"[WIREFRAME] Enemy {i+1}: {pos_info}")
                else:
                    add_event_log("[ENEMIES] No enemy ships in this system")
                    log_debug(f"[WIREFRAME] No enemy objects found in system {current_system}")
                    if system_type == "STAR+PLANET" and enemy_count_expected > 0:
                        add_event_log("[WARNING] Expected enemies but none found!")
                        log_debug(f"[WIREFRAME] WARNING: Expected {enemy_count_expected} enemies but found 0 in {system_type} system")
                
                # Mark as scanned if it wasn't already
                if current_system not in game_state.scan.scanned_systems:
                    game_state.scan.scanned_systems.add(current_system)

        # Update player ship position (orbital or linear movement)
        if game_state.map_mode == 'system':
            if game_state.orbital.player_orbiting_planet and game_state.orbital.player_orbit_center is not None:
                # Update orbital animation
                dt = clock.get_time() / 1000.0
                game_state.orbital.orbital_angle += game_state.orbital.orbital_speed * dt
                
                # Update the planet's position (since planets orbit stars)
                # Find the specific planet that the player is orbiting using the stored key
                if player_orbit_key is not None:
                    target_orbit = next((orbit for orbit in planet_orbits if (orbit['star'], orbit['planet']) == player_orbit_key), None)
                    if target_orbit:
                        star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
                        if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
                            star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
                            hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
                            orbit_radius_px = target_orbit['hex_radius'] * hex_size
                            angle = planet_anim_state.get(player_orbit_key, target_orbit['angle'])
                            planet_px = star_px + orbit_radius_px * math.cos(angle)
                            planet_py = star_py + orbit_radius_px * math.sin(angle)
                            
                            # Update the orbit center to follow the planet
                            game_state.orbital.player_orbit_center = (planet_px, planet_py)
                
                # Calculate player ship position in orbit around planet
                system_ship_anim_x = game_state.orbital.player_orbit_center[0] + game_state.orbital.orbital_radius * math.cos(game_state.orbital.orbital_angle)
                system_ship_anim_y = game_state.orbital.player_orbit_center[1] + game_state.orbital.orbital_radius * math.sin(game_state.orbital.orbital_angle)
                
            elif system_ship_moving and system_dest_q is not None and system_dest_r is not None:
                # Regular movement animation
                player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                if player_obj is not None:
                    now = pygame.time.get_ticks()
                    elapsed = now - system_move_start_time if system_move_start_time is not None else 0
                    # Use system trajectory start position if available, otherwise fall back to player hex position
                    if system_trajectory_start_x is not None and system_trajectory_start_y is not None:
                        start_x, start_y = system_trajectory_start_x, system_trajectory_start_y
                    else:
                        start_x, start_y = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                    end_x, end_y = hex_grid.get_hex_center(system_dest_q, system_dest_r)
                    t = min(elapsed / system_move_duration_ms, 1.0)
                    system_ship_anim_x = start_x + (end_x - start_x) * t
                    system_ship_anim_y = start_y + (end_y - start_y) * t
                    if t >= 1.0:
                        # Arrived at destination
                        system_ship_anim_x, system_ship_anim_y = end_x, end_y
                        
                        # Calculate and consume energy for the impulse movement
                        dx = abs(system_dest_q - player_obj.system_q)
                        dy = abs(system_dest_r - player_obj.system_r)
                        distance = max(dx, dy)
                        base_energy_cost = distance * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
                        energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                        player_ship.consume_energy(energy_cost)
                        
                        player_obj.system_q = system_dest_q
                        player_obj.system_r = system_dest_r
                        system_ship_moving = False
                        system_move_start_time = None
                        
                        # Stop movement sound when impulse completes
                        sound_manager.stop_movement_sound()
                        system_trajectory_start_x, system_trajectory_start_y = None, None  # Reset system trajectory tracking
                        add_event_log(f"Arrived at system hex ({system_dest_q}, {system_dest_r}) - Energy: {player_ship.warp_core_energy}/{player_ship.max_warp_core_energy}")
                        print(f"System ship arrived at hex ({system_dest_q}, {system_dest_r}), consumed {energy_cost} energy")
                        
                        # Check for starbase docking at this hex
                        system_objects = systems.get(current_system, [])
                        for obj in system_objects:
                            if obj.type == 'starbase':
                                # Check if player is at the starbase center hex
                                if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                                    if obj.system_q == system_dest_q and obj.system_r == system_dest_r:
                                        # Player is at starbase center - this is main docking port
                                        add_event_log("*** DOCKING WITH STARBASE - MAIN PORT ***")
                                        add_event_log("Ship systems fully repaired, energy restored, and torpedoes replenished!")
                                        player_ship.reset_damage()  # Full repair
                                        player_ship.regenerate_energy()  # Full energy restore
                                        sound_manager.play_sound('scanner')  # Use scanner sound for docking
                                        break
                                else:
                                    # Calculate if player is on one of the 6 surrounding docking pad hexes
                                    # The 6 hexes surrounding the starbase center in a flat-topped hex grid
                                    starbase_center_q = obj.system_q if hasattr(obj, 'system_q') else 10  # Default center
                                    starbase_center_r = obj.system_r if hasattr(obj, 'system_r') else 10
                                    
                                    # Define the 6 adjacent hex positions around the starbase center
                                    docking_pad_positions = [
                                        (starbase_center_q + 1, starbase_center_r),     # East
                                        (starbase_center_q - 1, starbase_center_r),     # West  
                                        (starbase_center_q, starbase_center_r + 1),     # Southeast
                                        (starbase_center_q, starbase_center_r - 1),     # Northwest
                                        (starbase_center_q + 1, starbase_center_r - 1), # Northeast
                                        (starbase_center_q - 1, starbase_center_r + 1)  # Southwest
                                    ]
                                    
                                    if (system_dest_q, system_dest_r) in docking_pad_positions:
                                        # Player is at a docking pad
                                        pad_number = docking_pad_positions.index((system_dest_q, system_dest_r)) + 1
                                        add_event_log(f"*** DOCKING WITH STARBASE - PAD {pad_number} ***")
                                        add_event_log("Ship systems fully repaired, energy restored, and torpedoes replenished!")
                                        player_ship.reset_damage()  # Full repair
                                        player_ship.regenerate_energy()  # Full energy restore
                                        sound_manager.play_sound('scanner')  # Use scanner sound for docking
                                        break
                        
                        # Check if there's a pending orbital request
                        if pending_orbit_center is not None and pending_orbit_key is not None:
                            # Start orbiting the planet we moved to
                            game_state.orbital.player_orbiting_planet = True
                            game_state.orbital.player_orbit_center = pending_orbit_center
                            player_orbit_key = pending_orbit_key
                            game_state.orbital.orbital_angle = 0.0
                            add_event_log(f"Entering orbit around planet at ({system_dest_q}, {system_dest_r})")
                            
                            # Clear pending orbit
                            pending_orbit_center = None
                            pending_orbit_key = None

        # Draw destination indicator (red circle)
        if game_state.animation.ship_moving and game_state.animation.dest_q is not None and game_state.animation.dest_r is not None and game_state.map_mode == 'sector':
            dest_x, dest_y = hex_grid.get_hex_center(game_state.animation.dest_q, game_state.animation.dest_r)
            pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)
        # Draw system map destination indicator
        if system_ship_moving and system_dest_q is not None and system_dest_r is not None and game_state.map_mode == 'system':
            dest_x, dest_y = hex_grid.get_hex_center(system_dest_q, system_dest_r)
            pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)

        # --- Phaser animation drawing ---
        phaser_anim_data = game_state.weapon_animation_manager.get_phaser_animation_data(current_time)
        if phaser_anim_data and phaser_anim_data['active']:
            # Find player and enemy positions
            player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
            if player_obj is not None:
                # Use animated position (orbital or movement) if available, otherwise use static position
                if system_ship_anim_x is not None and system_ship_anim_y is not None:
                    px1, py1 = system_ship_anim_x, system_ship_anim_y
                else:
                    px1, py1 = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                px2, py2 = get_enemy_current_position(phaser_anim_data['target_enemy'], hex_grid)
                # Draw a thick laser line (yellow/red)
                color = (255, 255, 0) if (current_time // 100) % 2 == 0 else (255, 0, 0)
                pygame.draw.line(screen, color, (int(px1), int(py1)), (int(px2), int(py2)), 4)

        # --- Torpedo animation drawing ---
        torpedo_anim_data = game_state.weapon_animation_manager.get_torpedo_animation_data(current_time)
        if torpedo_anim_data:
            if torpedo_anim_data['state'] == 'traveling':
                # Draw torpedo as a bright white circle (larger and more visible)
                torpedo_x, torpedo_y = torpedo_anim_data['position']
                pygame.draw.circle(screen, (255, 255, 255), (int(torpedo_x), int(torpedo_y)), 6)
                # Add a bright trail effect
                pygame.draw.circle(screen, (255, 255, 0), (int(torpedo_x), int(torpedo_y)), 8, 2)
                # Add inner glow
                pygame.draw.circle(screen, (255, 255, 255), (int(torpedo_x), int(torpedo_y)), 3)
            elif torpedo_anim_data['state'] == 'exploding':
                # Draw proximity explosion animation with multiple radiating waves
                target_x, target_y = torpedo_anim_data['position']
                waves = torpedo_anim_data.get('waves', [])
                
                # Draw each expanding wave with different colors and opacities
                for wave in waves:
                    radius = wave['radius']
                    opacity = wave['opacity']
                    wave_index = wave['wave_index']
                    
                    # Create color variation based on wave index
                    if wave_index == 0:
                        # Core explosion - white hot
                        color = (255, 255, 255, min(opacity, 255))
                    elif wave_index == 1:
                        # Primary blast - yellow
                        color = (255, 255, 0, min(opacity, 255))
                    elif wave_index == 2:
                        # Secondary blast - orange
                        color = (255, 150, 0, min(opacity, 255))
                    else:
                        # Outer waves - red
                        color = (255, 50, 0, min(opacity, 255))
                    
                    # Draw wave with fading edge effect
                    if radius > 0:
                        # Create temporary surface for alpha blending
                        wave_surface = pygame.Surface((int(radius * 2 + 10), int(radius * 2 + 10)), pygame.SRCALPHA)
                        wave_center = (int(radius + 5), int(radius + 5))
                        
                        # Draw the wave ring
                        pygame.draw.circle(wave_surface, color[:3] + (opacity,), wave_center, int(radius), max(2, int(radius / 10)))
                        
                        # Blit to main screen
                        screen.blit(wave_surface, (int(target_x - radius - 5), int(target_y - radius - 5)), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # OLD TORPEDO CODE (commented out for transition)
        elif False:  # game_state.combat.torpedo_flying:
            now = pygame.time.get_ticks()
            elapsed = now - game_state.combat.torpedo_anim_start
            # DEBUG: Add occasional debug output
            if elapsed % 1000 < 16:  # Print every ~1 second for a few frames
                print(f"[DEBUG] Torpedo animation active: elapsed={elapsed}ms")
            
            if game_state.combat.torpedo_start_pos and game_state.combat.torpedo_target_pos:
                start_x, start_y = game_state.combat.torpedo_start_pos
                target_x, target_y = game_state.combat.torpedo_target_pos
                
                # Calculate torpedo travel distance and time
                distance = math.hypot(target_x - start_x, target_y - start_y)
                travel_time = distance / game_state.combat.torpedo_speed * 1000  # Convert to milliseconds
                
                if elapsed < travel_time:
                    # Torpedo is still flying - interpolate position
                    progress = elapsed / travel_time
                    torpedo_x = start_x + (target_x - start_x) * progress
                    torpedo_y = start_y + (target_y - start_y) * progress
                    
                    # Torpedo animation (visual feedback only - no debug spam)
                    
                    # Draw torpedo as a bright white circle (larger and more visible)
                    pygame.draw.circle(screen, (255, 255, 255), (int(torpedo_x), int(torpedo_y)), 6)
                    # Add a bright trail effect
                    pygame.draw.circle(screen, (255, 255, 0), (int(torpedo_x), int(torpedo_y)), 8, 2)
                    # Add inner glow
                    pygame.draw.circle(screen, (255, 255, 255), (int(torpedo_x), int(torpedo_y)), 3)
                else:
                    # Torpedo has reached target - explode and show results
                    if game_state.combat.torpedo_target_enemy is not None and game_state.combat.torpedo_combat_result is not None:
                        # Use the combat result calculated when torpedo was launched
                        combat_result = game_state.combat.torpedo_combat_result
                        
                        # Determine if torpedo actually hits based on accuracy and distance
                        hit_chance = max(0, constants.PLAYER_TORPEDO_ACCURACY - (game_state.combat.torpedo_target_distance * 0.05))
                        torpedo_hits = random.random() < hit_chance
                        
                        # Handle combat results
                        if combat_result['success'] and torpedo_hits:
                            # Draw explosion animation
                            explosion_radius = 15 + (elapsed - travel_time) // 50  # Growing explosion
                            if explosion_radius <= 25:
                                pygame.draw.circle(screen, (255, 255, 0), (int(target_x), int(target_y)), explosion_radius, 3)
                                pygame.draw.circle(screen, (255, 100, 0), (int(target_x), int(target_y)), explosion_radius - 5, 2)
                            
                            # Apply damage and show results (only once)
                            if not hasattr(game_state.combat, 'torpedo_damage_shown'):
                                # Apply the calculated damage to the enemy
                                updated_combat_result = player_ship.apply_damage_to_enemy(game_state.combat.torpedo_target_enemy, combat_result)
                                
                                if combat_result['shield_damage'] > 0 and combat_result['hull_damage'] > 0:
                                    add_event_log(f"Torpedo hit! Shields: {combat_result['shield_damage']} Hull: {combat_result['hull_damage']}")
                                elif combat_result['shield_damage'] > 0:
                                    add_event_log(f"Torpedo hit shields for {combat_result['shield_damage']} damage")
                                elif combat_result['hull_damage'] > 0:
                                    add_event_log(f"Hull breach! Torpedo damage: {combat_result['hull_damage']}")
                                
                                # Update scan panel with current enemy status after damage is applied
                                torpedo_enemy_id = None
                                for eid, enemy_obj in game_state.combat.targeted_enemies.items():
                                    if enemy_obj is game_state.combat.torpedo_target_enemy:
                                        torpedo_enemy_id = eid
                                        break
                                
                                if torpedo_enemy_id and torpedo_enemy_id in enemy_scan_panel.scanned_enemies:
                                    # Update scan data with actual enemy status after damage
                                    enemy_scan_panel.scanned_enemies[torpedo_enemy_id]['hull'] = updated_combat_result['target_health']
                                    enemy_scan_panel.scanned_enemies[torpedo_enemy_id]['max_hull'] = updated_combat_result['target_max_health']
                                    enemy_scan_panel.scanned_enemies[torpedo_enemy_id]['shields'] = updated_combat_result['target_shields']
                                    enemy_scan_panel.scanned_enemies[torpedo_enemy_id]['max_shields'] = updated_combat_result['target_max_shields']
                                
                                if combat_result['target_destroyed']:
                                    add_event_log("Enemy ship destroyed by torpedo!")
                                    systems[current_system].remove(game_state.combat.torpedo_target_enemy)
                                    # Remove from targeting system
                                    destroyed_id = None
                                    for tid, tobj in game_state.combat.targeted_enemies.items():
                                        if tobj is game_state.combat.torpedo_target_enemy:
                                            destroyed_id = tid
                                            break
                                    
                                    if destroyed_id:
                                        del game_state.combat.targeted_enemies[destroyed_id]
                                        # Remove from enemy popups if exists
                                        if destroyed_id in game_state.scan.enemy_popups:
                                            del game_state.scan.enemy_popups[destroyed_id]
                                            add_event_log(f"Target {destroyed_id} destroyed - popup closed")
                                        # Remove from enemy scan panel
                                        enemy_scan_panel.remove_scan_result(destroyed_id)
                                        add_event_log(f"Enemy {destroyed_id} scan data removed")
                                    
                                    # Auto-select next available target if any remain
                                    if game_state.combat.targeted_enemies:
                                        # Get the first available enemy from targeted_enemies
                                        next_enemy_id = next(iter(game_state.combat.targeted_enemies.keys()))
                                        game_state.combat.selected_enemy = game_state.combat.targeted_enemies[next_enemy_id]
                                        add_event_log(f"Auto-targeting {next_enemy_id}")
                                        print(f"[DEBUG] Auto-selected enemy {next_enemy_id} as new target")
                                    else:
                                        game_state.combat.selected_enemy = None
                                        add_event_log("No targets remaining")
                                
                                game_state.combat.torpedo_damage_shown = True
                        elif combat_result['success'] and not torpedo_hits:
                            # Torpedo launched successfully but missed target
                            if not hasattr(game_state.combat, 'torpedo_damage_shown'):
                                add_event_log("Torpedo missed target!")
                                game_state.combat.torpedo_damage_shown = True
                        else:
                            # Torpedo system failed to launch
                            if not hasattr(game_state.combat, 'torpedo_damage_shown'):
                                add_event_log("Torpedo launch failed!")
                                game_state.combat.torpedo_damage_shown = True
                    
                    # End animation after explosion
                    if elapsed > travel_time + 500:  # 500ms explosion duration
                        game_state.stop_torpedo_animation()
                        if hasattr(game_state.combat, 'torpedo_damage_shown'):
                            delattr(game_state.combat, 'torpedo_damage_shown')

        # --- Enemy weapon animation drawing ---
        game_state.weapon_animation_manager.draw_enemy_weapon_animations(screen, current_time)

        
        # Update scan positions for moving enemies
        update_enemy_scan_positions()

        # Update and draw enemy popups
        update_enemy_popups()
        for enemy_id, popup_info in game_state.scan.enemy_popups.items():
            draw_enemy_popup(popup_info)

        # Draw ship status display
        ship_status_display.draw(screen, player_ship)

        # Draw enemy scan panel with targeted enemy highlighting
        targeted_enemy_id = None
        if game_state.combat.selected_enemy is not None:
            # Find the enemy ID for the selected enemy object
            for enemy_id, enemy_obj in game_state.combat.targeted_enemies.items():
                if enemy_obj is game_state.combat.selected_enemy:
                    targeted_enemy_id = enemy_id
                    break
        enemy_scan_panel.draw(screen, targeted_enemy_id)

        pygame.display.flip()
        clock.tick(FPS)
        logging.debug(f"[LOOP] Frame complete. FPS: {clock.get_fps():.1f}")

except Exception as e:
    print("--- GAME CRASHED ---")
    traceback.print_exc()
    print(f"Error: {e}")
finally:
    pygame.quit()
    sys.exit() 