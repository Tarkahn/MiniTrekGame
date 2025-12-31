import pygame
import math
import sys
import os
import traceback
import logging
import random

# Adjust the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import debug logger
from debug_logger import log_debug

# No constants are currently used from data.constants, so removing the import

from galaxy_generation.object_placement import place_objects_by_system, generate_system_objects
from ui.hex_map import create_hex_grid_for_map
from ui.button_panel import draw_button_panel, handle_button_events
from ui.stardate import Stardate
from ui.background_loader import BackgroundAndStarLoader
from ui.hex_utils import get_star_hexes, get_planet_hexes
# Note: is_hex_blocked is defined locally as it uses module-level planet_anim_state
from ui.drawing_utils import get_star_color, get_planet_color
from ui.dialogs import show_game_over_screen
# show_orbit_dialog is now used via event_handler module
from ui.event_handler import (EventContext, EventResult, handle_button_click,
                               handle_toggle_click, handle_sector_map_click,
                               handle_system_map_click, handle_right_click)
from ui.renderer import (RenderContext, draw_status_bar,
                          draw_event_log_panel, draw_popup_dock, draw_image_display_panel,
                          draw_control_panel)
from ui.enemy_popups import (create_enemy_popup as _create_enemy_popup,
                              draw_enemy_popup, update_enemy_popups as _update_enemy_popups,
                              get_enemy_id as _get_enemy_id)
from ui.scan_functions import (perform_planet_scan as _perform_planet_scan,
                                perform_star_scan as _perform_star_scan,
                                perform_anomaly_scan as _perform_anomaly_scan,
                                perform_enemy_scan as _perform_enemy_scan,
                                get_enemy_current_position as _get_enemy_current_position,
                                update_enemy_scan_positions as _update_enemy_scan_positions,
                                update_enemy_scan_stats as _update_enemy_scan_stats)
from galaxy_generation.map_object import MapObject
from ui.sound_manager import get_sound_manager
from ui.ship_status_display import create_ship_status_display
from ui.enemy_scan_panel import create_enemy_scan_panel
from ui.communications_display import create_communications_display, EnemyCommunicationsManager
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

# Create ship status display (takes upper portion)
ship_status_x = map_size + event_log_width  # To the right of event log
ship_status_y = STATUS_HEIGHT
ship_status_width = SHIP_STATUS_WIDTH
COMMS_DISPLAY_HEIGHT = 200  # Height for communications display
ship_status_height = HEIGHT - STATUS_HEIGHT - COMMS_DISPLAY_HEIGHT
ship_status_display = create_ship_status_display(
    ship_status_x, ship_status_y,
    ship_status_width, ship_status_height,
    font
)

# Create communications display (below ship status)
comms_display_x = ship_status_x
comms_display_y = ship_status_y + ship_status_height
comms_display_width = SHIP_STATUS_WIDTH
comms_display = create_communications_display(
    comms_display_x, comms_display_y,
    comms_display_width, COMMS_DISPLAY_HEIGHT,
    font
)

# Create communications manager for enemy messages
comms_manager = EnemyCommunicationsManager(comms_display)

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

# Debug enemy placement - now split by faction
klingon_coords = lazy_object_coords.get('klingon', [])
romulan_coords = lazy_object_coords.get('romulan', [])
all_enemy_coords = klingon_coords + romulan_coords
log_debug(f"Total enemies placed: {len(all_enemy_coords)} ({len(klingon_coords)} Klingon, {len(romulan_coords)} Romulan)")
star_systems_with_enemies = [coord for coord in set(all_enemy_coords) if coord in star_coords]
log_debug(f"Star systems with enemies: {len(star_systems_with_enemies)} out of {len(star_coords)}")
log_debug(f"First 5 star systems with enemies: {star_systems_with_enemies[:5]}")
log_debug(f"First 10 Klingon coordinates: {klingon_coords[:10]}")
log_debug(f"First 10 Romulan coordinates: {romulan_coords[:10]}")

# Log which systems should have enemies
log_debug("=== SYSTEMS WITH ENEMIES (from placement) ===")
enemy_system_counts = {}
for coord in klingon_coords:
    if coord not in enemy_system_counts:
        enemy_system_counts[coord] = {'klingon': 0, 'romulan': 0}
    enemy_system_counts[coord]['klingon'] += 1
for coord in romulan_coords:
    if coord not in enemy_system_counts:
        enemy_system_counts[coord] = {'klingon': 0, 'romulan': 0}
    enemy_system_counts[coord]['romulan'] += 1
for coord, counts in sorted(enemy_system_counts.items())[:10]:
    is_star = coord in star_coords
    has_planets = any(orbit['star'] == coord for orbit in planet_orbits)
    system_type = "STAR+PLANET" if is_star and has_planets else "STAR" if is_star else "EMPTY"
    log_debug(f"  {coord}: {counts['klingon']} Klingon, {counts['romulan']} Romulan ({system_type})")

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

# Connect communications manager to combat manager for enemy messages
player_ship.combat_manager.set_comms_manager(comms_manager)

# Configure LLM for dynamic enemy communications (optional)
# Load API key from environment variable or .env file
def load_openai_api_key():
    """Load OpenAI API key from environment or .env file."""
    # First check environment variable
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and api_key != 'paste-your-key-here':
        return api_key

    # Try to load from .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
                        key = line.split('=', 1)[1].strip()
                        if key and key != 'paste-your-key-here':
                            return key
        except Exception as e:
            print(f"[COMMS] Error reading .env file: {e}")
    return None

openai_api_key = load_openai_api_key()
if openai_api_key:
    comms_manager.configure_llm(
        api_key=openai_api_key,
        endpoint="https://api.openai.com/v1/chat/completions",
        model="gpt-3.5-turbo"  # Fast and cheap, or use "gpt-4" for better quality
    )
    print("[COMMS] LLM-powered enemy communications enabled!")
else:
    print("[COMMS] No API key found - using pre-written messages (set OPENAI_API_KEY in .env file)")

# Set initial state from player position
game_state.current_system = (ship_q, ship_r)
current_system = game_state.current_system
game_state.set_ship_position(ship_q, ship_r, hex_grid)

# Mark starting system as scanned so navigation works immediately
game_state.scan.scanned_systems.add(current_system)

# Track currently scanned celestial object
current_scanned_object = None
current_scanned_image = None

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

# Button panel parameters - sized to fit 5 buttons in control panel
BUTTON_W, BUTTON_H = 110, 28
BUTTON_GAP = 8
TOGGLE_BTN_W, TOGGLE_BTN_H = 130, 28
# Calculate TOGGLE_BTN_Y to fit within the window
# We have 5 buttons, each 28px tall with 8px gaps = 36px per button
# Add spacer (40px) between Control Panel label and buttons
CONTROL_PANEL_LABEL_SPACER = 40
TOGGLE_BTN_Y = bottom_pane_y + CONTROL_PANEL_LABEL_SPACER
BUTTON_COLOR = (100, 100, 180)

# Button rectangles for click detection
button_rects, toggle_btn_rect = [], None

# --- Print button labels and indices at startup ---
# Button labels matching button_panel.py
button_labels = ["Move", "Fire", "Torpedo", "Scan", "Repairs"]
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

# Color generation functions imported from ui.drawing_utils:
# get_star_color, get_planet_color

# Wrapper functions for enemy popup module
def create_enemy_popup(enemy_id, enemy_obj):
    """Create a popup window for enemy ship stats."""
    return _create_enemy_popup(enemy_id, enemy_obj, game_state, map_size,
                               RIGHT_EVENT_LOG_WIDTH, STATUS_HEIGHT,
                               font, small_font, title_font)

def update_enemy_popups():
    """Update and clean up enemy popups for destroyed ships."""
    _update_enemy_popups(game_state, systems, enemy_scan_panel, add_event_log)

def get_enemy_id(enemy_obj):
    """Get or assign a unique ID to an enemy object."""
    return _get_enemy_id(enemy_obj, game_state)

# show_game_over_screen imported from ui.dialogs

# Wrapper functions for scan module
def perform_enemy_scan(enemy_obj, enemy_id):
    """Perform a detailed scan of an enemy and add results to scan panel."""
    _perform_enemy_scan(enemy_obj, enemy_id, systems, game_state,
                        enemy_scan_panel, add_event_log, sound_manager, player_ship)

def get_enemy_current_position(enemy_obj, hex_grid):
    """Get the current position of an enemy (animated if moving, otherwise static)."""
    return _get_enemy_current_position(enemy_obj, hex_grid, player_ship)

def update_enemy_scan_positions():
    """Update scan panel positions for all scanned enemies that are moving."""
    _update_enemy_scan_positions(enemy_scan_panel, systems, game_state,
                                 player_ship, get_enemy_id)

def update_enemy_scan_stats():
    """Update scan panel stats (hull, shields, energy) for all scanned enemies."""
    _update_enemy_scan_stats(enemy_scan_panel, systems, game_state,
                             player_ship, get_enemy_id)

# Hex utility functions imported from ui.hex_utils:
# get_hex_neighbors, get_star_hexes, get_planet_hexes

# is_hex_blocked defined locally because it uses module-level planet_anim_state
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

# show_orbit_dialog imported from ui.dialogs

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
from data.constants import PLAYER_PHASER_RANGE
phaser_range = PLAYER_PHASER_RANGE

# wrap_text imported from ui.text_utils

def perform_planet_scan(planet_q, planet_r):
    """Perform a detailed scan of a planet and display results."""
    global current_scanned_object, current_scanned_image
    scan_data, planet_image = _perform_planet_scan(planet_q, planet_r, current_system,
                                                    add_event_log, sound_manager)
    current_scanned_object = scan_data
    current_scanned_image = planet_image


def perform_star_scan(star_q, star_r):
    """Perform a detailed scan of a star and display results."""
    global current_scanned_object, current_scanned_image
    scan_data, star_image = _perform_star_scan(star_q, star_r, current_system,
                                                add_event_log, sound_manager)
    current_scanned_object = scan_data
    current_scanned_image = star_image


def perform_anomaly_scan(anomaly_obj):
    """Perform a detailed scan of an anomaly and display results."""
    global current_scanned_object, current_scanned_image
    scan_data, anomaly_image = _perform_anomaly_scan(anomaly_obj, current_system,
                                                      add_event_log, sound_manager)
    current_scanned_object = scan_data
    current_scanned_image = anomaly_image


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

# Enemy weapon animation function removed - enemies are static decorative objects

# Add initial welcome message
add_event_log("Welcome to Star Trek Tactical Game")
add_event_log("Click to navigate, scan for objects")

# Create event context for the event handler
# Note: Some values (map_rect, button_rects, toggle_btn_rect) are set inside the game loop
event_ctx = EventContext()
event_ctx.game_state = game_state
event_ctx.player_ship = player_ship
event_ctx.systems = systems
event_ctx.current_system = current_system
event_ctx.hex_grid = hex_grid
event_ctx.screen = screen
event_ctx.font = font
event_ctx.button_rects = None  # Set inside game loop
event_ctx.toggle_btn_rect = None  # Set inside game loop
event_ctx.button_labels = button_labels
event_ctx.map_rect = None  # Set inside game loop
event_ctx.ship_status_display = ship_status_display
event_ctx.enemy_scan_panel = enemy_scan_panel
event_ctx.comms_display = comms_display
event_ctx.comms_manager = comms_manager
event_ctx.sound_manager = sound_manager
event_ctx.star_coords = star_coords
event_ctx.lazy_object_coords = lazy_object_coords
event_ctx.planet_orbits = planet_orbits
event_ctx.planet_anim_state = planet_anim_state
event_ctx.ship_q = ship_q
event_ctx.ship_r = ship_r
event_ctx.phaser_range = phaser_range
event_ctx.add_event_log = add_event_log
event_ctx.create_enemy_popup = create_enemy_popup
event_ctx.perform_enemy_scan = perform_enemy_scan
event_ctx.perform_planet_scan = perform_planet_scan
event_ctx.perform_star_scan = perform_star_scan
event_ctx.perform_anomaly_scan = perform_anomaly_scan
event_ctx.get_enemy_id = get_enemy_id
event_ctx.get_enemy_current_position = get_enemy_current_position
event_ctx.is_hex_blocked = is_hex_blocked

# Set up weapon animation manager callback for evasion messages
if game_state.weapon_animation_manager:
    game_state.weapon_animation_manager.add_event_log = add_event_log

# Create render context for the renderer module
render_ctx = RenderContext()
render_ctx.screen = screen
render_ctx.font = font
render_ctx.label_font = label_font
render_ctx.title_font = title_font
render_ctx.small_font = small_font
render_ctx.width = WIDTH
render_ctx.height = HEIGHT
render_ctx.map_x = map_x
render_ctx.map_y = map_y
render_ctx.map_size = map_size
render_ctx.status_height = STATUS_HEIGHT
render_ctx.event_log_x = event_log_x
render_ctx.event_log_y = event_log_y
render_ctx.event_log_width = event_log_width
render_ctx.event_log_height = event_log_height
render_ctx.bottom_pane_y = bottom_pane_y
render_ctx.bottom_pane_height = bottom_pane_height
render_ctx.image_display_width = image_display_width
render_ctx.control_panel_width = control_panel_width
render_ctx.popup_dock_x = event_log_x + event_log_width
render_ctx.enemy_scan_width = ENEMY_SCAN_WIDTH
render_ctx.color_status = COLOR_STATUS
render_ctx.color_map = COLOR_MAP
render_ctx.color_event_log = COLOR_EVENT_LOG
render_ctx.color_event_log_border = COLOR_EVENT_LOG_BORDER
render_ctx.color_image_display = COLOR_IMAGE_DISPLAY
render_ctx.color_control_panel = COLOR_CONTROL_PANEL
render_ctx.color_button_area_border = COLOR_BUTTON_AREA_BORDER
render_ctx.color_text = COLOR_TEXT
render_ctx.hex_outline = HEX_OUTLINE
render_ctx.game_state = game_state
render_ctx.player_ship = player_ship
render_ctx.hex_grid = hex_grid
render_ctx.background_loader = background_and_star_loader
render_ctx.stardate_system = stardate_system
render_ctx.systems = systems
render_ctx.star_coords = star_coords
render_ctx.planet_orbits = planet_orbits
render_ctx.lazy_object_coords = lazy_object_coords
render_ctx.current_system = current_system
render_ctx.planet_anim_state = planet_anim_state
render_ctx.planet_images_assigned = planet_images_assigned
render_ctx.planet_colors = planet_colors
render_ctx.event_log_max_lines = EVENT_LOG_MAX_LINES
render_ctx.control_panel_label_spacer = CONTROL_PANEL_LABEL_SPACER

try:
    running = True
    while running:
        screen.fill(COLOR_BG)
        
        # Update weapon animations and handle combat events
        current_time = pygame.time.get_ticks()
        weapon_events = game_state.weapon_animation_manager.update(current_time, hex_grid)
        
        # Update enemy weapon animations (visual effects and damage application)
        game_state.weapon_animation_manager.update_enemy_animations(current_time)
        
        # Update ship systems and enemy AI continuously 
        delta_time = clock.get_time() / 1000.0  # Convert milliseconds to seconds
        
        # Update player ship systems (shields, energy regeneration, repairs)
        if hasattr(player_ship, 'update'):
            player_ship.update(delta_time)
        else:
            # Fallback for older code structure
            if hasattr(player_ship, 'shield_system'):
                player_ship.shield_system.update(delta_time)
            if hasattr(player_ship, 'update_repairs'):
                player_ship.update_repairs(delta_time)

        # Update player ship critical state (hull breach, warp core breach countdown)
        if hasattr(player_ship, 'update_critical_state') and player_ship.ship_state != "operational":
            player_ship.update_critical_state(delta_time)
        
        # Check for game over condition
        if hasattr(player_ship, 'ship_state') and player_ship.ship_state == "destroyed":
            # Show game over screen
            show_game_over_screen(screen, player_ship.name)
            # Game over screen will exit the program
        
        # Update enemy AI (movement animations, tactical decisions)
        player_ship.combat_manager.update_enemy_ai(delta_time, systems, game_state.current_system, hex_grid, player_ship)
        
        # Handle weapon combat events
        if weapon_events['phaser_completed']:
            phaser_event = weapon_events['phaser_completed']
            combat_result = phaser_event['combat_result']  # Use the updated result with damage info
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
                # Safely remove enemy from system (may already be removed by splash damage)
                if phaser_event['target_enemy'] in systems[current_system]:
                    systems[current_system].remove(phaser_event['target_enemy'])
                if enemy_id:
                    enemy_scan_panel.remove_scan_result(enemy_id)
                game_state.combat.selected_enemy = None
        
        # Handle direct torpedo hits (for static enemies)
        if weapon_events['torpedo_explosion']:
            torpedo_event = weapon_events['torpedo_explosion']
            combat_result = torpedo_event['combat_result']
            target_enemy = torpedo_event['target_enemy']
            
            # Log torpedo direct hit
            if combat_result['shield_damage'] > 0 and combat_result['hull_damage'] > 0:
                add_event_log(f"Torpedo direct hit! Shields: {combat_result['shield_damage']} Hull: {combat_result['hull_damage']}")
            elif combat_result['shield_damage'] > 0:
                add_event_log(f"Torpedo hit shields for {combat_result['shield_damage']} damage")
            elif combat_result['hull_damage'] > 0:
                add_event_log(f"Hull breach! Torpedo damage: {combat_result['hull_damage']}")
            else:
                add_event_log(f"Torpedo hit - Absorbed by shields")
            
            # Update scan panel for the target enemy
            enemy_id = None
            for eid, enemy_obj in game_state.combat.targeted_enemies.items():
                if enemy_obj is target_enemy:
                    enemy_id = eid
                    break
            
            if enemy_id and enemy_id in enemy_scan_panel.scanned_enemies:
                enemy_scan_panel.scanned_enemies[enemy_id]['shields'] = combat_result['target_shields']
                enemy_scan_panel.scanned_enemies[enemy_id]['hull'] = combat_result['target_health']
                enemy_scan_panel.scanned_enemies[enemy_id]['max_hull'] = combat_result['target_max_health']
                enemy_scan_panel.scanned_enemies[enemy_id]['max_shields'] = combat_result['target_max_shields']
            
            # Check if target destroyed
            if combat_result['target_destroyed']:
                add_event_log("Enemy ship destroyed!")
                # Safely remove enemy from system (may already be removed by splash damage)
                if target_enemy in systems[current_system]:
                    systems[current_system].remove(target_enemy)
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

        # Handle player caught in own torpedo blast
        if weapon_events.get('torpedo_player_hit'):
            player_hit = weapon_events['torpedo_player_hit']
            damage = player_hit['damage']
            distance_pixels = player_hit['distance_pixels']
            ring_index = player_hit['ring_index']

            ring_names = ["Core Blast", "Primary Wave", "Secondary Wave", "Tertiary Wave", "Pressure Wave", "Outer Shockwave"]
            ring_name = ring_names[min(ring_index, len(ring_names)-1)]

            add_event_log(f"*** WARNING: Own torpedo {ring_name} hit our ship! ***")
            add_event_log(f"Distance from explosion: {distance_pixels:.0f}px - Damage taken: {damage}")

            # Check if player ship was destroyed
            if not player_ship.is_alive():
                add_event_log("*** CRITICAL: Ship destroyed by own torpedo! ***")

        # Status/Tooltip Panel (top) - using renderer module
        draw_status_bar(render_ctx)

        # Main Map Area (perfect square, flush left)
        map_rect = pygame.Rect(map_x, map_y, map_size, map_size)
        pygame.draw.rect(screen, COLOR_MAP, map_rect)

        # --- Removed map mode label as requested ---

        # Draw background image (lowest layer) - different for sector vs system map
        if game_state.map_mode == 'sector':
            # Sector map uses SectorBackground.png at 30% opacity
            background_img = background_and_star_loader.get_scaled_sector_background(map_size, map_size, opacity=0.3)
        else:
            # System maps use MapBackground.jpg at full opacity
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
                                obj.scaled_star_image = background_and_star_loader.scale_star_image(obj.star_image, hex_grid.radius * 4.5)
                            
                            if obj.scaled_star_image:
                                # Center the image
                                image_rect = obj.scaled_star_image.get_rect()
                                image_rect.center = (int(center_x), int(center_y))
                                screen.blit(obj.scaled_star_image, image_rect)
                            else:
                                # Fallback to circle if image scaling failed
                                if not hasattr(obj, 'color'):
                                    obj.color = get_star_color()
                                pygame.draw.circle(screen, obj.color, (int(center_x), int(center_y)), int(hex_grid.radius * 4.5))
                        else:
                            # Fallback to circle if no image available
                            if not hasattr(obj, 'color'):
                                obj.color = get_star_color()
                            pygame.draw.circle(screen, obj.color, (int(center_x), int(center_y)), int(hex_grid.radius * 4.5))

        # Draw the hex grid with conditional transparency based on map mode
        # Sector map: More visible for fog of war navigation, System map: Barely visible for clean aesthetics
        grid_alpha = 64 if game_state.map_mode == 'sector' else 20
        hex_grid.draw_grid(screen, HEX_OUTLINE, alpha=grid_alpha)

        # Draw coordinate labels along the edges
        hex_grid.draw_coordinate_labels(screen, small_font, color=(120, 120, 150))

        # --- FOG OF WAR OVERLAY (draw early to hide objects) ---
        # Only apply fog of war to sector map, not system maps
        if game_state.map_mode == 'sector':
            for row in range(hex_grid.rows):
                for col in range(hex_grid.cols):
                    if (col, row) not in game_state.scan.scanned_systems:
                        cx, cy = hex_grid.get_hex_center(col, row)
                        hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=25)

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

                # Ensure anomaly systems are generated for sector map display (for testing)
                if 'anomaly' in lazy_object_coords:
                    for anomaly_coord in lazy_object_coords['anomaly']:
                        if anomaly_coord not in systems:
                            # Generate the missing anomaly system
                            from galaxy_generation.object_placement import generate_system_objects
                            anomaly_objects = generate_system_objects(
                                anomaly_coord[0], anomaly_coord[1],
                                lazy_object_coords,
                                star_coords=star_coords,
                                planet_orbits=planet_orbits,
                                grid_size=hex_grid.cols
                            )
                            systems[anomaly_coord] = anomaly_objects

                # NOTE: Don't add planet coordinates - they orbit around stars, they don't have their own systems
                green_dots_drawn = 0
                for q, r in occupied_hexes:
                    px, py = hex_grid.get_hex_center(q, r)
                    
                    # Check if this system contains a starbase or anomaly
                    system_has_starbase = False
                    system_has_anomaly = False
                    system_objects = systems.get((q, r), [])
                    for obj in system_objects:
                        if obj.type == 'starbase':
                            system_has_starbase = True
                        elif obj.type == 'anomaly':
                            system_has_anomaly = True

                    # Draw dot with appropriate color
                    # Light green for starbase, purple/magenta for anomaly, default gray for others
                    if system_has_starbase:
                        dot_color = (144, 238, 144)  # Light green
                    elif system_has_anomaly:
                        dot_color = (180, 0, 255)  # Purple/magenta for anomalies
                    else:
                        dot_color = (100, 100, 130)  # Default gray
                    pygame.draw.circle(
                        screen, dot_color, (int(px), int(py)), 6
                    )
        else:
            # Ensure we have objects for the current system (generate but don't show until scanned)
            if current_system not in systems:
                # Debug check before generation
                expected_klingons = lazy_object_coords.get('klingon', []).count(current_system)
                expected_romulans = lazy_object_coords.get('romulan', []).count(current_system)
                expected_enemies = expected_klingons + expected_romulans
                is_star = current_system in star_coords
                has_planets = any(orbit['star'] == current_system for orbit in planet_orbits)
                add_event_log(f"[RENDER GEN] Generating system {current_system}")
                add_event_log(f"[RENDER GEN] Type: {'STAR+PLANET' if is_star and has_planets else 'STAR' if is_star else 'EMPTY'}")
                add_event_log(f"[RENDER GEN] Expected enemies: {expected_enemies} ({expected_klingons} Klingon, {expected_romulans} Romulan)")

                # Debug: Check the exact data being passed
                if expected_enemies > 0:
                    log_debug(f"[RENDER] System {current_system} should have {expected_enemies} enemies")
                    klingon_list = lazy_object_coords.get('klingon', [])
                    romulan_list = lazy_object_coords.get('romulan', [])
                    if klingon_list or romulan_list:
                        add_event_log(f"[DEBUG] Klingon list length: {len(klingon_list)}, Romulan list length: {len(romulan_list)}")
                        add_event_log(f"[DEBUG] Count of {current_system}: {klingon_list.count(current_system)} Klingon, {romulan_list.count(current_system)} Romulan")
                        log_debug(f"[RENDER] Enemies at {current_system}: {klingon_list.count(current_system)} Klingon, {romulan_list.count(current_system)} Romulan")
                    else:
                        add_event_log(f"[DEBUG] Enemy lists are empty!")
                        log_debug(f"[RENDER] ERROR: Enemy lists are empty!")
                
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
                            # Get current position from dynamic EnemyShip AI or static position
                            render_px, render_py = get_enemy_current_position(obj, hex_grid)

                            # Get faction from enemy object (defaults to klingon)
                            enemy_faction = getattr(obj, 'faction', None) or 'klingon'

                            # Check if this is a cloaked Romulan ship
                            enemy_id = id(obj)
                            is_cloaked = False
                            is_flashing = False
                            if hasattr(player_ship, 'combat_manager') and enemy_id in player_ship.combat_manager.enemy_ships:
                                enemy_ship = player_ship.combat_manager.enemy_ships[enemy_id]
                                is_cloaked = getattr(enemy_ship, 'is_cloaked', False)
                                is_flashing = getattr(enemy_ship, '_is_flashing', False)
                                # Check is_visible property for rendering decision
                                if hasattr(enemy_ship, 'is_visible') and not enemy_ship.is_visible:
                                    # Cloaked and not flashing - skip rendering entirely
                                    continue

                            # Use faction-specific ship image if available, otherwise fallback to triangle
                            enemy_img = background_and_star_loader.get_enemy_ship_image(faction=enemy_faction)
                            if enemy_img:
                                scaled_enemy = background_and_star_loader.scale_ship_image(enemy_img, hex_grid.radius, faction=enemy_faction)
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
                                        if enemy_ship.is_moving and enemy_ship.target_position:
                                            # Enemy is moving - calculate rotation based on current position to final destination
                                            current_pos = (render_px, render_py)
                                            dest_pos = hex_grid.get_hex_center(enemy_ship.target_position[0], enemy_ship.target_position[1])
                                            new_target_rotation = background_and_star_loader.calculate_movement_angle(current_pos, dest_pos)
                                            obj.target_rotation = new_target_rotation
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

                                    # Apply flashing effect for cloaked ships hit by torpedo
                                    if is_flashing and enemy_faction == 'romulan':
                                        # Create a flashing effect by modulating alpha
                                        flash_surface = rotated_enemy.copy()
                                        # Flicker between visible and semi-transparent
                                        import time as time_module
                                        flicker_speed = 10  # Flickers per second
                                        flicker = int(time_module.time() * flicker_speed) % 2
                                        if flicker == 0:
                                            flash_surface.set_alpha(255)  # Fully visible
                                        else:
                                            flash_surface.set_alpha(128)  # Semi-transparent
                                        img_rect = flash_surface.get_rect(center=(int(render_px), int(render_py)))
                                        screen.blit(flash_surface, img_rect)
                                    else:
                                        img_rect = rotated_enemy.get_rect(center=(int(render_px), int(render_py)))
                                        screen.blit(rotated_enemy, img_rect)
                                else:
                                    # Fallback to triangle if scaling fails
                                    # Romulans are green, Klingons are red
                                    color = (0, 200, 0) if enemy_faction == 'romulan' else (255, 0, 0)
                                    size = 12 if enemy_faction == 'romulan' else 8  # Romulans larger
                                    pygame.draw.polygon(screen, color, [
                                        (int(render_px), int(render_py)-size),
                                        (int(render_px)-int(size*0.75), int(render_py)+int(size*0.5)),
                                        (int(render_px)+int(size*0.75), int(render_py)+int(size*0.5))
                                    ])
                            else:
                                # Fallback to triangle if image not available
                                # Romulans are green, Klingons are red
                                color = (0, 200, 0) if enemy_faction == 'romulan' else (255, 0, 0)
                                size = 12 if enemy_faction == 'romulan' else 8  # Romulans larger
                                pygame.draw.polygon(screen, color, [
                                    (int(render_px), int(render_py)-size),
                                    (int(render_px)-int(size*0.75), int(render_py)+int(size*0.5)),
                                    (int(render_px)+int(size*0.75), int(render_py)+int(size*0.5))
                                ])
                        elif obj.type == 'anomaly':
                            # Get anomaly type from props, or use a random one
                            anomaly_type = obj.props.get('anomaly_type', None)
                            if anomaly_type:
                                anomaly_img = background_and_star_loader.get_anomaly_image_by_name(anomaly_type)
                            else:
                                anomaly_img = background_and_star_loader.get_random_anomaly_image()

                            if anomaly_img:
                                # Scale anomaly image - make them LARGE and dangerous looking
                                # Stars are sized at radius * 4.5 * 4 = radius * 18
                                # Anomalies should be 2x star size, so use multiplier of 30 (1.2 * 30 = 36)
                                scaled_anomaly = background_and_star_loader.scale_anomaly_image(anomaly_img, hex_grid.radius, 30.0)
                                if scaled_anomaly:
                                    # Center the image on the hex position
                                    img_rect = scaled_anomaly.get_rect(center=(int(px), int(py)))
                                    screen.blit(scaled_anomaly, img_rect)
                            else:
                                # Fallback to magenta circle if image not available
                                # Match the scaled anomaly size (2x star size)
                                color = (255, 0, 255)
                                pygame.draw.circle(screen, color, (int(px), int(py)), int(hex_grid.radius * 4.5 * 2))
                        elif obj.type == 'player':
                            # Only draw player ship if it's not destroyed
                            if hasattr(player_ship, 'ship_state') and player_ship.ship_state == "destroyed":
                                # Ship is destroyed - don't draw it
                                continue
                            
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


        # Update render context with current scanned object state
        render_ctx.current_scanned_object = current_scanned_object
        render_ctx.current_scanned_image = current_scanned_image

        # Side panels - using renderer module
        draw_event_log_panel(render_ctx)
        draw_popup_dock(render_ctx)
        draw_image_display_panel(render_ctx)
        draw_control_panel(render_ctx)
        
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

        # Update event context with current state each frame
        event_ctx.current_system = current_system
        event_ctx.ship_q = ship_q
        event_ctx.ship_r = ship_r
        event_ctx.system_ship_anim_x = system_ship_anim_x
        event_ctx.system_ship_anim_y = system_ship_anim_y
        event_ctx.system_ship_moving = system_ship_moving
        event_ctx.map_rect = map_rect
        event_ctx.button_rects = button_rects
        event_ctx.toggle_btn_rect = toggle_btn_rect

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
                    # Use event handler module for button clicks
                    handle_button_click(label, event_ctx)

                if toggle_clicked:
                    print("Toggle button clicked")
                    handle_toggle_click(event_ctx)

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
                    # Use event handler for sector map navigation
                    event_result = EventResult()
                    if handle_sector_map_click(mx, my, event_ctx, event_result):
                        # Apply any trajectory state changes
                        if event_result.trajectory_start_x is not None:
                            trajectory_start_x = event_result.trajectory_start_x
                            trajectory_start_y = event_result.trajectory_start_y
                elif map_rect.collidepoint(mx, my) and game_state.map_mode == 'system' and current_system in game_state.scan.scanned_systems:
                    # Use event handler for system map navigation
                    event_result = EventResult()
                    if handle_system_map_click(mx, my, event_ctx, event_result):
                        # Apply any state changes from the result
                        if event_result.player_orbit_key is not None:
                            player_orbit_key = event_result.player_orbit_key
                        if event_result.pending_orbit_center is not None:
                            pending_orbit_center = event_result.pending_orbit_center
                            pending_orbit_key = event_result.pending_orbit_key
                        if event_result.system_ship_moving is not None:
                            system_ship_moving = event_result.system_ship_moving
                        if event_result.system_dest_q is not None:
                            system_dest_q = event_result.system_dest_q
                            system_dest_r = event_result.system_dest_r
                        if event_result.system_move_start_time is not None:
                            system_move_start_time = event_result.system_move_start_time
                        if event_result.system_move_duration_ms is not None:
                            system_move_duration_ms = event_result.system_move_duration_ms
                        if event_result.system_trajectory_start_x is not None:
                            system_trajectory_start_x = event_result.system_trajectory_start_x
                            system_trajectory_start_y = event_result.system_trajectory_start_y
                        if event_result.system_ship_anim_x is not None:
                            system_ship_anim_x = event_result.system_ship_anim_x
                            system_ship_anim_y = event_result.system_ship_anim_y

            # Right-click: target enemy in system mode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
                mx, my = event.pos
                if map_rect.collidepoint(mx, my):
                    # Use event handler for right-click targeting/scanning
                    handle_right_click(mx, my, event_ctx)

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
            new_x = start_x + (end_x - start_x) * t
            new_y = start_y + (end_y - start_y) * t

            # Calculate distance traveled this frame and deduct energy continuously
            if game_state.animation.last_anim_x is not None and game_state.animation.last_anim_y is not None:
                frame_distance = math.hypot(new_x - game_state.animation.last_anim_x,
                                           new_y - game_state.animation.last_anim_y)
                game_state.animation.accumulated_pixel_distance += frame_distance

                # Convert accumulated pixel distance to hex distance and deduct energy
                hex_size_pixels = hex_grid.radius * 1.5  # Approximate hex size
                hex_distance_traveled = game_state.animation.accumulated_pixel_distance / hex_size_pixels

                # Deduct energy for each full hex traveled
                if hex_distance_traveled >= 1.0:
                    hexes_to_charge = int(hex_distance_traveled)
                    base_energy_cost = hexes_to_charge * constants.WARP_ENERGY_COST
                    energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                    player_ship.consume_energy(energy_cost)
                    # Subtract the charged distance from accumulated
                    game_state.animation.accumulated_pixel_distance -= hexes_to_charge * hex_size_pixels

            # Update position tracking
            game_state.animation.last_anim_x = new_x
            game_state.animation.last_anim_y = new_y
            game_state.animation.ship_anim_x = new_x
            game_state.animation.ship_anim_y = new_y

            if t >= 1.0:
                # Arrived at destination
                game_state.animation.ship_anim_x, game_state.animation.ship_anim_y = end_x, end_y

                # Deduct any remaining accumulated distance as final energy cost
                if game_state.animation.accumulated_pixel_distance > 0:
                    hex_size_pixels = hex_grid.radius * 1.5
                    remaining_hexes = game_state.animation.accumulated_pixel_distance / hex_size_pixels
                    if remaining_hexes >= 0.5:  # Charge for partial hex if at least half
                        base_energy_cost = constants.WARP_ENERGY_COST
                        energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                        player_ship.consume_energy(energy_cost)
                    game_state.animation.accumulated_pixel_distance = 0.0

                ship_q, ship_r = game_state.animation.dest_q, game_state.animation.dest_r
                game_state.animation.ship_moving = False
                game_state.animation.move_start_time = None
                game_state.animation.last_anim_x = None
                game_state.animation.last_anim_y = None

                # Stop movement sound when warp completes
                sound_manager.stop_movement_sound()
                trajectory_start_x, trajectory_start_y = None, None  # Reset trajectory tracking
                logging.info(f"[MOVE] Ship arrived at ({ship_q}, {ship_r})")
                add_event_log(f"Arrived at sector ({ship_q}, {ship_r}) - Energy: {int(player_ship.warp_core_energy)}/{int(player_ship.max_warp_core_energy)}")
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
                
                # Store the expected enemy count for later (combine both factions)
                enemy_count_expected = (
                    lazy_object_coords.get('klingon', []).count(current_system) +
                    lazy_object_coords.get('romulan', []).count(current_system)
                )

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
                    klingon_check = lazy_object_coords.get('klingon', []).count(current_system)
                    romulan_check = lazy_object_coords.get('romulan', []).count(current_system)
                    enemy_check = klingon_check + romulan_check
                    add_event_log(f"[DEBUG] Before generate: {klingon_check} Klingon, {romulan_check} Romulan")
                    add_event_log(f"[DEBUG] lazy_object_coords keys: {list(lazy_object_coords.keys())}")
                    log_debug(f"[WIREFRAME] Before generate_system_objects: {enemy_check} enemies")
                    log_debug(f"[WIREFRAME] lazy_object_coords keys: {list(lazy_object_coords.keys())}")
                    log_debug(f"[WIREFRAME] Klingon list length: {len(lazy_object_coords.get('klingon', []))}")
                    log_debug(f"[WIREFRAME] Romulan list length: {len(lazy_object_coords.get('romulan', []))}")
                    
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
                
                # Update weapon animation manager with current system objects immediately
                # This ensures torpedo splash damage works even before manual scan
                if game_state.weapon_animation_manager:
                    game_state.weapon_animation_manager.system_objects = systems.get(current_system, [])

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
                    new_sys_x = start_x + (end_x - start_x) * t
                    new_sys_y = start_y + (end_y - start_y) * t

                    # Calculate distance traveled this frame and deduct energy continuously
                    if game_state.animation.system_last_anim_x is not None and game_state.animation.system_last_anim_y is not None:
                        frame_distance = math.hypot(new_sys_x - game_state.animation.system_last_anim_x,
                                                   new_sys_y - game_state.animation.system_last_anim_y)
                        game_state.animation.system_accumulated_pixel_distance += frame_distance

                        # Convert accumulated pixel distance to hex distance and deduct energy
                        hex_size_pixels = hex_grid.radius * 1.5  # Approximate hex size
                        hex_distance_traveled = game_state.animation.system_accumulated_pixel_distance / hex_size_pixels

                        # Deduct energy for each full hex traveled
                        if hex_distance_traveled >= 1.0:
                            hexes_to_charge = int(hex_distance_traveled)
                            base_energy_cost = hexes_to_charge * constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
                            energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                            player_ship.consume_energy(energy_cost)
                            # Subtract the charged distance from accumulated
                            game_state.animation.system_accumulated_pixel_distance -= hexes_to_charge * hex_size_pixels

                    # Update position tracking
                    game_state.animation.system_last_anim_x = new_sys_x
                    game_state.animation.system_last_anim_y = new_sys_y
                    system_ship_anim_x = new_sys_x
                    system_ship_anim_y = new_sys_y

                    if t >= 1.0:
                        # Arrived at destination
                        system_ship_anim_x, system_ship_anim_y = end_x, end_y

                        # Deduct any remaining accumulated distance as final energy cost
                        if game_state.animation.system_accumulated_pixel_distance > 0:
                            hex_size_pixels = hex_grid.radius * 1.5
                            remaining_hexes = game_state.animation.system_accumulated_pixel_distance / hex_size_pixels
                            if remaining_hexes >= 0.5:  # Charge for partial hex if at least half
                                base_energy_cost = constants.LOCAL_MOVEMENT_ENERGY_COST_PER_HEX
                                energy_cost = player_ship.get_movement_energy_cost(base_energy_cost)
                                player_ship.consume_energy(energy_cost)
                            game_state.animation.system_accumulated_pixel_distance = 0.0

                        player_obj.system_q = system_dest_q
                        player_obj.system_r = system_dest_r
                        system_ship_moving = False
                        system_move_start_time = None
                        game_state.animation.system_last_anim_x = None
                        game_state.animation.system_last_anim_y = None

                        # Stop movement sound when impulse completes
                        sound_manager.stop_movement_sound()
                        system_trajectory_start_x, system_trajectory_start_y = None, None  # Reset system trajectory tracking
                        add_event_log(f"Arrived at system hex ({system_dest_q}, {system_dest_r}) - Energy: {int(player_ship.warp_core_energy)}/{int(player_ship.max_warp_core_energy)}")
                        print(f"System ship arrived at hex ({system_dest_q}, {system_dest_r})")
                        
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
                            # Calculate initial orbital angle based on ship's arrival position
                            dx = system_ship_anim_x - pending_orbit_center[0]
                            dy = system_ship_anim_y - pending_orbit_center[1]
                            initial_angle = math.atan2(dy, dx)

                            game_state.orbital.player_orbiting_planet = True
                            game_state.orbital.player_orbit_center = pending_orbit_center
                            player_orbit_key = pending_orbit_key
                            game_state.orbital.orbital_angle = initial_angle
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

        # Draw torpedo target hex indicator (orange/yellow pulsing crosshair)
        if game_state.map_mode == 'system':
            torpedo_target = game_state.get_torpedo_target_hex()
            if torpedo_target is not None:
                target_q, target_r = torpedo_target
                target_x, target_y = hex_grid.get_hex_center(target_q, target_r)

                # Pulsing effect based on time
                pulse = abs(math.sin(current_time / 200.0))  # Oscillates 0 to 1
                base_radius = 12
                pulse_radius = int(base_radius + pulse * 4)

                # Draw concentric circles (orange/yellow)
                pygame.draw.circle(screen, (255, 165, 0), (int(target_x), int(target_y)), pulse_radius, 2)
                pygame.draw.circle(screen, (255, 255, 0), (int(target_x), int(target_y)), 6, 2)

                # Draw crosshair lines
                line_len = pulse_radius + 4
                pygame.draw.line(screen, (255, 165, 0),
                                (int(target_x - line_len), int(target_y)),
                                (int(target_x - 6), int(target_y)), 2)
                pygame.draw.line(screen, (255, 165, 0),
                                (int(target_x + 6), int(target_y)),
                                (int(target_x + line_len), int(target_y)), 2)
                pygame.draw.line(screen, (255, 165, 0),
                                (int(target_x), int(target_y - line_len)),
                                (int(target_x), int(target_y - 6)), 2)
                pygame.draw.line(screen, (255, 165, 0),
                                (int(target_x), int(target_y + 6)),
                                (int(target_x), int(target_y + line_len)), 2)

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
                                
                                if updated_combat_result['shield_damage'] > 0 and updated_combat_result['hull_damage'] > 0:
                                    add_event_log(f"Torpedo hit! Shields: {updated_combat_result['shield_damage']} Hull: {updated_combat_result['hull_damage']}")
                                elif updated_combat_result['shield_damage'] > 0:
                                    add_event_log(f"Torpedo hit shields for {updated_combat_result['shield_damage']} damage")
                                elif updated_combat_result['hull_damage'] > 0:
                                    add_event_log(f"Hull breach! Torpedo damage: {updated_combat_result['hull_damage']}")
                                
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
        # Determine actual player render position for accurate targeting
        player_render_pos = None
        if game_state.map_mode == 'system':
            # System mode - use system animation position if available, otherwise static position
            if 'system_ship_anim_x' in locals() and system_ship_anim_x is not None and system_ship_anim_y is not None:
                player_render_pos = (system_ship_anim_x, system_ship_anim_y)
            else:
                # Fallback to static player position
                player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                if player_obj:
                    player_render_pos = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
        elif game_state.map_mode == 'sector':
            # Sector mode - use sector animation position if available
            if hasattr(game_state.animation, 'ship_anim_x') and game_state.animation.ship_anim_x is not None and game_state.animation.ship_anim_y is not None:
                player_render_pos = (game_state.animation.ship_anim_x, game_state.animation.ship_anim_y)
        
        game_state.weapon_animation_manager.draw_enemy_weapon_animations(screen, current_time, hex_grid, player_render_pos)

        
        # Update scan positions for moving enemies
        update_enemy_scan_positions()

        # Update scan panel stats (hull, shields, energy) in real-time
        update_enemy_scan_stats()

        # Update and draw enemy popups
        update_enemy_popups()
        for enemy_id, popup_info in game_state.scan.enemy_popups.items():
            draw_enemy_popup(screen, popup_info)

        # Draw ship status display
        ship_status_display.draw(screen, player_ship)

        # Draw communications display
        comms_display.draw(screen)

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