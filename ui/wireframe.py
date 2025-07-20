import pygame
import math
import sys
import os
import traceback
import logging
import random

# Adjust the path to ensure imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# No constants are currently used from data.constants, so removing the import

from galaxy_generation.object_placement import place_objects_by_system, generate_system_objects
from ui.hex_map import create_hex_grid_for_map
from ui.button_panel import draw_button_panel, handle_button_events
from galaxy_generation.map_object import MapObject

# Calculate compact window dimensions based on layout needs
RIGHT_EVENT_LOG_WIDTH = 300
BOTTOM_PANEL_HEIGHT = 200
STATUS_HEIGHT = 40
# Calculate minimum width needed: map + event log panel
map_size = min(980, 960 - STATUS_HEIGHT - BOTTOM_PANEL_HEIGHT)  # Targeting ~720px map
WIDTH = map_size + RIGHT_EVENT_LOG_WIDTH
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
font = pygame.font.SysFont(None, 28)
label_font = pygame.font.SysFont(None, 22)  # Smaller font for panel labels

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
print(f"[LAYOUT DEBUG] WIDTH={WIDTH}, HEIGHT={HEIGHT}")
print(f"[LAYOUT DEBUG] map_size={map_size}, bottom_pane_y={bottom_pane_y}")
print(f"[LAYOUT DEBUG] bottom_pane_height={bottom_pane_height}")
print(f"[LAYOUT DEBUG] image_display_width={image_display_width}, control_panel_width={control_panel_width}")
print(f"[LAYOUT DEBUG] event_log_x={event_log_x}, event_log_y={event_log_y}, event_log_width={event_log_width}, event_log_height={event_log_height}")

# TOGGLE_BTN_Y will be calculated after button parameters are defined

# Create the hex grid
hex_grid = create_hex_grid_for_map(map_x, map_y, map_size, 20, 20)

# Generate map objects by system (now returns systems, star_coords, lazy_object_coords, planet_orbits)
systems, star_coords, lazy_object_coords, planet_orbits = place_objects_by_system()

# Debug output for verification
print(f"[DEBUG] Number of stars: {len(star_coords)}")
print(f"[DEBUG] Number of planets: {len(planet_orbits)}")
print(f"[DEBUG] Star coordinates: {list(star_coords)[:5]}...")  # Show first 5
if planet_orbits:
    print(f"[DEBUG] Sample planet orbit: {planet_orbits[0]}")
    # Check which stars have planets
    stars_with_planets = set(orbit['star'] for orbit in planet_orbits)
    print(f"[DEBUG] Stars with planets: {stars_with_planets}")

# Set initial player position from lazy_object_coords['player']
player_hexes = list(lazy_object_coords['player'])
if player_hexes:
    ship_q, ship_r = player_hexes[0]
    current_system = (ship_q, ship_r)
else:
    ship_q, ship_r = 0, 0
    current_system = (0, 0)

# Ensure systems[current_system] always contains at least a star object
if current_system not in systems or not any(obj.type == 'star' for obj in systems[current_system]):
    print(f"[INIT] Adding missing star object to systems at {current_system}")
    systems[current_system] = [MapObject('star', ship_q, ship_r)]

# Ensure only one player object exists in the starting system
if not any(obj.type == 'player' for obj in systems[current_system]):
    systems[current_system].append(MapObject('player', ship_q, ship_r))

print(f"[INIT] ship_q: {ship_q}, ship_r: {ship_r}, current_system: {current_system}")
print(f"[INIT] star_coords: {star_coords}")
print(f"[INIT] lazy_object_coords: {lazy_object_coords}")
print(f"[INIT] systems: {systems}")

# Map mode state
map_mode = 'sector'  # or 'system'

# Scan states
sector_scan_active = False
scanned_systems = set()

# Button panel parameters
BUTTON_W, BUTTON_H = 110, 35
BUTTON_GAP = 15
TOGGLE_BTN_W, TOGGLE_BTN_H = 130, 35
# Calculate TOGGLE_BTN_Y to fit within the window
# We have 3 buttons (removed End Turn), each 35px tall with 15px gaps
# Add significant spacer (50px) between Control Panel label and buttons
CONTROL_PANEL_LABEL_SPACER = 50
TOGGLE_BTN_Y = bottom_pane_y + CONTROL_PANEL_LABEL_SPACER
print(f"[DEBUG] Calculated TOGGLE_BTN_Y={TOGGLE_BTN_Y} (window height={HEIGHT})")
BUTTON_COLOR = (100, 100, 180)

# Button state tracking (3 buttons now)
button_pressed = [False, False, False]
toggle_btn_pressed = [False]  # Use list for mutability in handler
button_rects, toggle_btn_rect = [], None

# --- Print button labels and indices at startup ---
# Button labels (removed End Turn button)
button_labels = ["Move", "Fire", "Scan"]
for idx, label in enumerate(button_labels):
    print(f"[DEBUG] Button {idx}: {label}")

# Animated position (float, in pixels)
ship_anim_x, ship_anim_y = hex_grid.get_hex_center(ship_q, ship_r)

# Destination hex (None if not moving)
dest_q, dest_r = None, None
ship_moving = False

# Calculate max distance for ship speed
corner1 = hex_grid.get_hex_center(0, 0)
corner2 = hex_grid.get_hex_center(19, 19)
max_distance = math.hypot(corner2[0] - corner1[0], corner2[1] - corner1[1])

FPS = 60
SHIP_SPEED = max_distance / (2 * FPS)  # pixels per frame for 2s travel

# Remove global SHIP_SPEED, use per-move speed
move_ship_speed = None  # pixels per frame for current move
move_frames = 2 * FPS  # 2 seconds at 60 FPS

# Persistent system object state for scanned systems (for future save/load)
system_object_states = {}

clock = pygame.time.Clock()
move_start_time = None  # Time when movement started (in ms)
move_duration_ms = 2000  # Always 2 seconds

# Event log for displaying messages
EVENT_LOG_MAX_LINES = 25  # Increased to accommodate wrapped text

event_log = []

# Track last system for debug print
last_debug_system = None

# Planet animation state dictionary
planet_anim_state = { (orbit['star'], orbit['planet']): orbit['angle'] for orbit in planet_orbits }
# Planet color storage
planet_colors = {}

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

# --- Player ship orbital state ---
player_orbiting_planet = False
player_orbit_center = None  # Planet position (px, py)
player_orbit_key = None     # (star, planet) key to track which planet we're orbiting
player_orbit_radius = 60    # Orbit radius in pixels
player_orbit_angle = 0.0    # Current angle
player_orbit_speed = 0.4    # Radians per second (reduced for more realistic movement)
system_ship_moving = False
system_move_start_time = None
system_move_duration_ms = 1000  # 1 second for system moves

# --- Phaser firing state ---
selected_enemy = None
phaser_animating = False
phaser_anim_start = 0
phaser_anim_duration = 500  # ms
phaser_pulse_count = 5
phaser_damage = 40
phaser_range = 9

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
            event_log.append(line.strip())
    
    # Keep within max lines limit
    while len(event_log) > EVENT_LOG_MAX_LINES:
        event_log.pop(0)

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

# Add initial welcome message
add_event_log("Welcome to Star Trek Tactical Game")
add_event_log("Click to navigate, scan for objects")

try:
    running = True
    while running:
        screen.fill(COLOR_BG)
        # Status/Tooltip Panel (top)
        status_rect = pygame.Rect(0, 0, WIDTH, STATUS_HEIGHT)
        pygame.draw.rect(screen, COLOR_STATUS, status_rect)
        status_label = label_font.render('Status/Tooltip Panel', True, COLOR_TEXT)
        screen.blit(status_label, (10, 8))
        # FPS Counter
        fps = clock.get_fps()
        fps_label = font.render(f'FPS: {fps:.1f}', True, COLOR_TEXT)
        screen.blit(fps_label, (WIDTH - 120, 8))

        # Main Map Area (perfect square, flush left)
        map_rect = pygame.Rect(map_x, map_y, map_size, map_size)
        pygame.draw.rect(screen, COLOR_MAP, map_rect)
        map_label = label_font.render('Sector/System Map (20x20)', True, COLOR_TEXT)
        screen.blit(map_label, (map_x + 20, map_y + 20))

        # --- MAP LABEL (show current map mode) ---
        map_mode_label = label_font.render(
            f"{'Sector Map' if map_mode == 'sector' else 'System Map'}",
            True, COLOR_TEXT
        )
        screen.blit(
            map_mode_label,
            (map_x + map_size // 2 - 60, map_y + 8)
        )

        # Draw the hex grid
        hex_grid.draw_grid(screen, HEX_OUTLINE)

        # --- FOG OF WAR OVERLAY (draw early to hide objects) ---
        # Only apply fog of war to sector map, not system maps
        if map_mode == 'sector':
            for row in range(hex_grid.rows):
                for col in range(hex_grid.cols):
                    if (col, row) not in scanned_systems:
                        cx, cy = hex_grid.get_hex_center(col, row)
                        hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=153)

        # Draw objects on the grid
        if map_mode == 'sector':
            # Only draw system indicators if a sector scan has been done
            if sector_scan_active:
                # Show indicator for any hex that has actual systems (not individual planets)
                # Stars have systems, lazy objects have systems, but planets orbit around stars elsewhere
                occupied_hexes = set(star_coords)
                for coords_set in lazy_object_coords.values():
                    occupied_hexes.update(coords_set)
                # NOTE: Don't add planet coordinates - they orbit around stars, they don't have their own systems
                for q, r in occupied_hexes:
                    px, py = hex_grid.get_hex_center(q, r)
                    pygame.draw.circle(
                        screen, (100, 100, 130), (int(px), int(py)), 6
                    )
                logging.debug(f"[SECTOR] Drawing indicators for {len(occupied_hexes)} occupied hexes.")
        else:
            # Ensure we have objects for the current system (generate but don't show until scanned)
            if current_system not in systems:
                # Generate objects for this system if they don't exist
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
                add_event_log(f"[GEN] Generated {len(system_objs)} objects for system {current_system}")
                obj_types = [obj.type for obj in system_objs]
                add_event_log(f"  Object types: {', '.join(obj_types)}")
            
            # Draw all objects (fog of war removed for system maps)
            # Draw stars that occupy 4 hexes
            for obj in systems.get(current_system, []):
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
                        # Get or generate star color
                        if not hasattr(obj, 'color'):
                            obj.color = get_star_color()
                        # Draw star as single uniform circle (doubled size)
                        pygame.draw.circle(screen, obj.color, (int(center_x), int(center_y)), int(hex_grid.radius * 3.6))
                
            # Animate and draw all planets associated with stars in this system
            planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
            if last_debug_system != current_system:
                print(f"[DEBUG] System {current_system} has {len(planets_in_system)} planets.")
                print(f"[DEBUG] Total planet_orbits: {len(planet_orbits)}")
                print(f"[DEBUG] First few orbits: {planet_orbits[:3] if planet_orbits else 'None'}")
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
                # Get or generate planet color
                planet_key = (orbit['star'], orbit['planet'])
                if planet_key not in planet_colors:
                    planet_colors[planet_key] = get_planet_color()
                planet_color = planet_colors[planet_key]
                
                # Draw planet as circle at exact position
                pygame.draw.circle(screen, planet_color, (int(planet_px), int(planet_py)), int(hex_grid.radius * 1.8))
            
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
                            color = (0, 0, 255)
                            pygame.draw.rect(screen, color, (int(px)-6, int(py)-6, 12, 12))
                        elif obj.type == 'enemy':
                            color = (255, 0, 0)
                            pygame.draw.polygon(screen, color, [
                                (int(px), int(py)-8),
                                (int(px)-6, int(py)+4),
                                (int(px)+6, int(py)+4)
                            ])
                        elif obj.type == 'anomaly':
                            color = (255, 0, 255)
                            pygame.draw.circle(screen, color, (int(px), int(py)), 5)
                        elif obj.type == 'player':
                            color = (0, 255, 255)
                            # Draw player ship at appropriate position
                            if (player_orbiting_planet or system_ship_moving) and system_ship_anim_x is not None and system_ship_anim_y is not None:
                                pygame.draw.circle(screen, color, (int(system_ship_anim_x), int(system_ship_anim_y)), 8)
                            else:
                                pygame.draw.circle(screen, color, (int(px), int(py)), 8)

        # Draw player ship
        if map_mode == 'sector':
            pygame.draw.circle(
                screen, (0, 255, 255), (int(ship_anim_x), int(ship_anim_y)), 8
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
        # Draw event log lines with text wrapping
        log_font = pygame.font.SysFont(None, 20)  # Slightly smaller font
        log_area_width = event_log_width - 40  # Account for padding
        y_offset = event_log_y + 50
        line_height = 20  # Tighter line spacing
        
        # Process and render each log entry with wrapping
        rendered_lines = 0
        for line in event_log[-EVENT_LOG_MAX_LINES:]:
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
        print(f"[DEBUG] Drawing buttons: TOGGLE_BTN_Y={TOGGLE_BTN_Y}")
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
            map_mode,
            TOGGLE_BTN_W,
            TOGGLE_BTN_H,
            TOGGLE_BTN_Y
        )
        if toggle_btn_rect:
            print(f"[DEBUG] Toggle button rect: {toggle_btn_rect}")

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle button events first
            if button_rects and toggle_btn_rect:
                (button_pressed,
                 toggle_btn_pressed,
                 clicked_index,
                 toggle_clicked) = handle_button_events(
                    event, button_rects, toggle_btn_rect, button_pressed,
                    toggle_btn_pressed
                )
                if clicked_index is not None:
                    label = button_labels[clicked_index] if clicked_index < len(button_labels) else str(clicked_index)
                    print(f"[DEBUG] Button {clicked_index} clicked: {label}")
                    # --- Use label-based action selection ---
                    if label == "Move":
                        add_event_log("Move mode: Click on a hex to navigate")
                    elif label == "Scan":
                        print("Scan initiated!")
                        if map_mode == 'sector':
                            sector_scan_active = True
                            add_event_log("Long-range sensors activated. All systems revealed.")
                            print("Sector scan active. All systems revealed.")
                        elif map_mode == 'system':
                            if current_system not in scanned_systems:
                                scanned_systems.add(current_system)
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
                                # Assign random system positions to all objects
                                for obj in system_objs:
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
                                            'hex_radius': random.randint(3, 9),  # Increased max distance to 9
                                            'angle': random.uniform(0, 2 * math.pi),
                                            'speed': random.uniform(0.02, 0.1)  # Speed in radians per second
                                        }
                                        planet_orbits.append(new_orbit)
                                        # Add to animation state
                                        planet_anim_state[(current_system, planet_coord)] = new_orbit['angle']
                                        logging.info(f"[SCAN] Added missing planet {planet_coord} to orbit around star {current_system}")
                                
                                systems[current_system] = system_objs
                                system_object_states[current_system] = [
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
                                        for q in range(hex_grid.cols):
                                            for r in range(hex_grid.rows):
                                                blocked, _ = is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid)
                                                if not blocked and (q, r) not in occupied:
                                                    player_obj = MapObject('player', current_system[0], current_system[1])
                                                    player_obj.system_q = q
                                                    player_obj.system_r = r
                                                    systems[current_system].append(player_obj)
                                                    break
                                            if player_obj:
                                                break
                                else:
                                    if not hasattr(player_obj, 'system_q') or not hasattr(player_obj, 'system_r'):
                                        occupied = set((getattr(obj, 'system_q', None), getattr(obj, 'system_r', None))
                                                       for obj in systems[current_system] if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'))
                                        max_attempts = 100
                                        for _ in range(max_attempts):
                                            rand_q = random.randint(0, hex_grid.cols - 1)
                                            rand_r = random.randint(0, hex_grid.rows - 1)
                                            # Check both occupied set and blocked hexes
                                            blocked, _ = is_hex_blocked(rand_q, rand_r, current_system, systems, planet_orbits, hex_grid)
                                            if (rand_q, rand_r) not in occupied and not blocked:
                                                player_obj.system_q = rand_q
                                                player_obj.system_r = rand_r
                                                break
                                        else:
                                            # Find any unblocked hex as fallback
                                            for q in range(hex_grid.cols):
                                                for r in range(hex_grid.rows):
                                                    blocked, _ = is_hex_blocked(q, r, current_system, systems, planet_orbits, hex_grid)
                                                    if not blocked and (q, r) not in occupied:
                                                        player_obj.system_q = q
                                                        player_obj.system_r = r
                                                        break
                                                if hasattr(player_obj, 'system_q'):
                                                    break
                                
                                # Count objects by type for a concise summary
                                obj_counts = {}
                                for obj in system_objs:
                                    obj_counts[obj.type] = obj_counts.get(obj.type, 0) + 1
                                
                                # Count planets associated with this star in planet_orbits
                                planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
                                planet_count = len(planets_in_system)
                                
                                # Create concise summary
                                if obj_counts or planet_count > 0:
                                    scan_parts = []
                                    for obj_type, count in obj_counts.items():
                                        scan_parts.append(f"{count} {obj_type}{'s' if count > 1 else ''}")
                                    
                                    if scan_parts:
                                        summary = f"System scan complete: {', '.join(scan_parts)}"
                                    else:
                                        summary = "System scan complete"
                                    
                                    if planet_count > 0:
                                        summary += f". {planet_count} planet{'s' if planet_count > 1 else ''} orbiting"
                                else:
                                    summary = "System scan complete: Empty space detected"
                                
                                add_event_log(summary)
                                print(
                                    f"System at {current_system} scanned. Objects revealed and state saved."
                                )
                            else:
                                print(f"System at {current_system} was already scanned.")
                    elif label == "Fire":
                        print(f"[DEBUG] Entered Fire button handler: map_mode={map_mode}, selected_enemy={selected_enemy}")
                        # Fire phasers at selected enemy (only works in system mode)
                        if map_mode == 'system':
                            print("[DEBUG] In system mode")
                            if selected_enemy is not None:
                                print(f"[DEBUG] selected_enemy is not None: {selected_enemy}")
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
                                if player_obj is not None and hasattr(player_obj, 'system_q') and hasattr(selected_enemy, 'system_q'):
                                    dx = selected_enemy.system_q - player_obj.system_q
                                    dy = selected_enemy.system_r - player_obj.system_r
                                    distance = math.hypot(dx, dy)
                                    print(f"[DEBUG] Player pos: ({player_obj.system_q}, {player_obj.system_r})")
                                    print(f"[DEBUG] Enemy pos: ({selected_enemy.system_q}, {selected_enemy.system_r})")
                                    print(f"[DEBUG] Phaser fire: distance={distance}")
                                    if distance <= phaser_range:
                                        print("[DEBUG] Enemy in range. Starting phaser animation.")
                                        phaser_animating = True
                                        phaser_anim_start = pygame.time.get_ticks()
                                        add_event_log(f"Firing phasers! Range: {distance:.1f} hexes")
                                    else:
                                        print("[DEBUG] Enemy out of range. No phaser animation.")
                                        add_event_log(f"Target out of range! Max range: {phaser_range} hexes")
                                else:
                                    add_event_log("No target selected! Right-click an enemy ship.")
                            else:
                                print("[DEBUG] selected_enemy is None")
                                add_event_log("No target selected! Right-click an enemy ship.")
                        else:
                            add_event_log("Weapons offline in sector view. Enter a system first.")

                if toggle_clicked:
                    print("Toggle button clicked")
                    new_mode = 'system' if map_mode == 'sector' else 'sector'
                    add_event_log(f"Switched to {new_mode} view")
                    map_mode = new_mode

            # Then handle map click events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if map_rect.collidepoint(mx, my) and map_mode == 'sector':
                    q, r = hex_grid.pixel_to_hex(mx, my)
                    if q is not None and r is not None:
                        dest_q, dest_r = q, r
                        ship_moving = True
                        move_start_time = pygame.time.get_ticks()
                        start_x, start_y = ship_anim_x, ship_anim_y
                        end_x, end_y = hex_grid.get_hex_center(dest_q, dest_r)
                        add_event_log(f"Setting course for sector ({q}, {r})")
                        print(f"Ship moving to hex ({q}, {r})")
                elif map_rect.collidepoint(mx, my) and map_mode == 'system' and current_system in scanned_systems:
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
                                    font = pygame.font.SysFont(None, 24)
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
                                                        # Start orbiting this planet
                                                        player_orbiting_planet = True
                                                        player_orbit_center = (planet_px, planet_py)
                                                        player_orbit_key = key
                                                        player_orbit_angle = 0.0
                                                        system_ship_moving = False  # Stop any current movement
                                                        add_event_log(f"Entering orbit around planet at ({q}, {r})")
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
                                if player_orbiting_planet:
                                    player_orbiting_planet = False
                                    player_orbit_center = None
                                    player_orbit_key = None
                                    add_event_log("Breaking orbit")
                                
                                system_dest_q, system_dest_r = q, r
                                system_ship_moving = True
                                system_move_start_time = pygame.time.get_ticks()
                                # Start position in pixels (from current animated position if orbiting)
                                if system_ship_anim_x is not None and system_ship_anim_y is not None:
                                    # Use current orbital position as starting point
                                    pass  # system_ship_anim_x and system_ship_anim_y are already set
                                else:
                                    system_ship_anim_x, system_ship_anim_y = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                                add_event_log(f"Setting course for system hex ({q}, {r})")
                                print(f"System ship moving to hex ({q}, {r})")
            
            # Right-click: select enemy in system mode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
                mx, my = event.pos
                if map_rect.collidepoint(mx, my) and map_mode == 'system':
                    q, r = hex_grid.pixel_to_hex(mx, my)
                    print(f"[DEBUG] Right-click at pixel=({mx},{my}), hex=({q},{r})")
                    print("[DEBUG] Enemy objects in current system:")
                    for obj in systems.get(current_system, []):
                        if obj.type == 'enemy' and hasattr(obj, 'system_q'):
                            print(f"  Enemy at ({obj.system_q}, {obj.system_r})")
                    if q is not None and r is not None:
                        # Find enemy at this hex
                        selected_enemy = None
                        for obj in systems.get(current_system, []):
                            if obj.type == 'enemy' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                                if obj.system_q == q and obj.system_r == r:
                                    selected_enemy = obj
                                    print(f"[DEBUG] Enemy selected at ({obj.system_q}, {obj.system_r})")
                                    add_event_log(f"Target acquired at ({q}, {r})")
                                    break
                        if selected_enemy is None:
                            add_event_log(f"No enemy at ({q}, {r})")

        # Update ship position (delta time based)
        if ship_moving and dest_q is not None and dest_r is not None:
            now = pygame.time.get_ticks()
            elapsed = now - move_start_time if move_start_time is not None else 0
            start_x, start_y = hex_grid.get_hex_center(ship_q, ship_r)
            end_x, end_y = hex_grid.get_hex_center(dest_q, dest_r)
            t = min(elapsed / move_duration_ms, 1.0)
            ship_anim_x = start_x + (end_x - start_x) * t
            ship_anim_y = start_y + (end_y - start_y) * t
            if t >= 1.0:
                # Arrived at destination
                ship_anim_x, ship_anim_y = end_x, end_y
                ship_q, ship_r = dest_q, dest_r
                ship_moving = False
                move_start_time = None
                logging.info(f"[MOVE] Ship arrived at ({ship_q}, {ship_r})")
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
                
                map_mode = 'system'
                current_system = (ship_q, ship_r)
                
                # Break orbital state when entering a new system
                if player_orbiting_planet:
                    player_orbiting_planet = False
                    player_orbit_center = None
                    player_orbit_key = None
                    system_ship_anim_x = None
                    system_ship_anim_y = None
                    add_event_log("Breaking orbit - entered new system")
                
                # Automatically scan the system when entering
                if current_system not in scanned_systems:
                    scanned_systems.add(current_system)
                    add_event_log(f"Auto-scanning system at ({ship_q}, {ship_r})...")
                    
                    # Debug: Show what objects are in this system
                    system_objects = systems.get(current_system, [])
                    planets_here = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
                    
                    # Show summary of objects in this system
                    add_event_log(f"[SCAN] System objects: {len(system_objects)} total")
                    obj_summary = {}
                    for obj in system_objects:
                        obj_summary[obj.type] = obj_summary.get(obj.type, 0) + 1
                    add_event_log(f"  Types: {dict(obj_summary)}")
                    
                    add_event_log(f"[SCAN] Planet orbits: {len(planets_here)} total")
                    if planets_here:
                        distances = [orbit['hex_radius'] for orbit in planets_here]
                        add_event_log(f"  Orbital distances: {sorted(distances)} hexes")
                    else:
                        add_event_log(f"  No planets in this system")
                
                # Generate or restore objects for this system
                if current_system not in systems:
                    system_objs = generate_system_objects(
                        current_system[0],
                        current_system[1],
                        lazy_object_coords,
                        star_coords=star_coords,
                        planet_orbits=planet_orbits,
                        grid_size=hex_grid.cols
                    )
                    systems[current_system] = system_objs
                    system_object_states[current_system] = [
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

        # Update player ship position (orbital or linear movement)
        if map_mode == 'system':
            if player_orbiting_planet and player_orbit_center is not None:
                # Update orbital animation
                dt = clock.get_time() / 1000.0
                player_orbit_angle += player_orbit_speed * dt
                
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
                            player_orbit_center = (planet_px, planet_py)
                
                # Calculate player ship position in orbit around planet
                system_ship_anim_x = player_orbit_center[0] + player_orbit_radius * math.cos(player_orbit_angle)
                system_ship_anim_y = player_orbit_center[1] + player_orbit_radius * math.sin(player_orbit_angle)
                
            elif system_ship_moving and system_dest_q is not None and system_dest_r is not None:
                # Regular movement animation
                player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
                if player_obj is not None:
                    now = pygame.time.get_ticks()
                    elapsed = now - system_move_start_time if system_move_start_time is not None else 0
                    start_x, start_y = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                    end_x, end_y = hex_grid.get_hex_center(system_dest_q, system_dest_r)
                    t = min(elapsed / system_move_duration_ms, 1.0)
                    system_ship_anim_x = start_x + (end_x - start_x) * t
                    system_ship_anim_y = start_y + (end_y - start_y) * t
                    if t >= 1.0:
                        # Arrived at destination
                        system_ship_anim_x, system_ship_anim_y = end_x, end_y
                        player_obj.system_q = system_dest_q
                        player_obj.system_r = system_dest_r
                        system_ship_moving = False
                        system_move_start_time = None
                        add_event_log(f"Arrived at system hex ({system_dest_q}, {system_dest_r})")
                        print(f"System ship arrived at hex ({system_dest_q}, {system_dest_r})")

        # Draw destination indicator (red circle)
        if ship_moving and dest_q is not None and dest_r is not None and map_mode == 'sector':
            dest_x, dest_y = hex_grid.get_hex_center(dest_q, dest_r)
            pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)
        # Draw system map destination indicator
        if system_ship_moving and system_dest_q is not None and system_dest_r is not None and map_mode == 'system':
            dest_x, dest_y = hex_grid.get_hex_center(system_dest_q, system_dest_r)
            pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)

        # --- Phaser animation drawing ---
        if phaser_animating and selected_enemy is not None:
            print("[DEBUG] Drawing phaser animation!")
            # Find player and enemy positions
            player_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
            if player_obj is not None:
                px1, py1 = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                px2, py2 = hex_grid.get_hex_center(selected_enemy.system_q, selected_enemy.system_r)
                now = pygame.time.get_ticks()
                elapsed = now - phaser_anim_start
                t = min(elapsed / phaser_anim_duration, 1.0)
                # Draw a thick laser line (yellow/red)
                color = (255, 255, 0) if (now // 100) % 2 == 0 else (255, 0, 0)
                pygame.draw.line(screen, color, (int(px1), int(py1)), (int(px2), int(py2)), 4)
                if t >= 1.0:
                    # Animation done, apply damage
                    if not hasattr(selected_enemy, 'health'):
                        selected_enemy.health = 100
                    selected_enemy.health -= phaser_damage
                    print(f"[DEBUG] Phaser hit! Enemy health now {selected_enemy.health}")
                    if selected_enemy.health <= 0:
                        add_event_log("Enemy ship destroyed!")
                        systems[current_system].remove(selected_enemy)
                        selected_enemy = None
                    phaser_animating = False

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