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

# Fixed window dimensions
WIDTH, HEIGHT = 1075, 1408

# Pane constants
STATUS_HEIGHT = 40
DOCKED_POPUP_WIDTH = 200

# Colors
COLOR_BG = (20, 20, 30)
COLOR_STATUS = (60, 60, 100)
COLOR_MAP = (40, 40, 60)
COLOR_EVENT_LOG = (30, 30, 50)
COLOR_CONTROL_PANEL = (50, 30, 30)
COLOR_DOCKED_POPUP = (80, 60, 60)
COLOR_TEXT = (220, 220, 220)
HEX_OUTLINE = (180, 180, 220)
HEX_BG = (40, 40, 60)
COLOR_MAP_DEBUG = (255, 0, 0)      # Red for map pane
COLOR_GRID_DEBUG = (0, 255, 0)     # Green for grid bounding box

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Star Trek Tactical Game - UI Wireframe')
font = pygame.font.SysFont(None, 28)

# Calculate layout once
map_size = min(WIDTH - DOCKED_POPUP_WIDTH, HEIGHT - STATUS_HEIGHT)
map_x = 0
map_y = STATUS_HEIGHT
bottom_pane_y = map_y + map_size
bottom_pane_height = HEIGHT - bottom_pane_y
event_log_width = map_size // 2
control_panel_width = map_size - event_log_width

# Create the hex grid
hex_grid = create_hex_grid_for_map(map_x, map_y, map_size, 20, 20)

# Generate map objects by system (now returns systems, star_coords, lazy_object_coords, planet_orbits)
systems, star_coords, lazy_object_coords, planet_orbits = place_objects_by_system()

# Debug output for verification
print(f"[DEBUG] Number of stars: {len(star_coords)}")
print(f"[DEBUG] Number of planets: {len(planet_orbits)}")
if planet_orbits:
    print(f"[DEBUG] Sample planet orbit: {planet_orbits[0]}")

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
BUTTON_W, BUTTON_H = 120, 40
BUTTON_GAP = 20
TOGGLE_BTN_W, TOGGLE_BTN_H = 200, 40
TOGGLE_BTN_Y = bottom_pane_y + 30 + 4 * (BUTTON_H + BUTTON_GAP)
BUTTON_COLOR = (100, 100, 180)

# Button state tracking
button_pressed = [False, False, False, False]
toggle_btn_pressed = [False]  # Use list for mutability in handler
button_rects, toggle_btn_rect = [], None

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

# --- System map movement state ---
system_ship_anim_x = None
system_ship_anim_y = None
system_dest_q = None
system_dest_r = None
system_ship_moving = False
system_move_start_time = None
system_move_duration_ms = 1000  # 1 second for system moves

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
        status_label = font.render('Status/Tooltip Panel', True, COLOR_TEXT)
        screen.blit(status_label, (10, 8))
        # FPS Counter
        fps = clock.get_fps()
        fps_label = font.render(f'FPS: {fps:.1f}', True, COLOR_TEXT)
        screen.blit(fps_label, (WIDTH - 120, 8))

        # Main Map Area (perfect square, flush left)
        map_rect = pygame.Rect(map_x, map_y, map_size, map_size)
        pygame.draw.rect(screen, COLOR_MAP, map_rect)
        map_label = font.render('Sector/System Map (20x20)', True, COLOR_TEXT)
        screen.blit(map_label, (map_x + 20, map_y + 20))

        # --- MAP LABEL (show current map mode) ---
        map_mode_label = font.render(
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
        if map_mode == 'sector':
            for row in range(hex_grid.rows):
                for col in range(hex_grid.cols):
                    if (col, row) not in scanned_systems:
                        cx, cy = hex_grid.get_hex_center(col, row)
                        hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=153)
        elif map_mode == 'system' and current_system not in scanned_systems:
            # Cover the entire system map with fog if not scanned
            for row in range(hex_grid.rows):
                for col in range(hex_grid.cols):
                    cx, cy = hex_grid.get_hex_center(col, row)
                    hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=200)

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
                # Assign random system positions to all objects
                for obj in system_objs:
                    obj.system_q = random.randint(0, hex_grid.cols - 1)
                    obj.system_r = random.randint(0, hex_grid.rows - 1)
                systems[current_system] = system_objs
                logging.info(f"[RENDER] Generated {len(system_objs)} objects for system {current_system}")
            
            # Draw all objects only if the system has been scanned
            if current_system in scanned_systems:
                # Draw stars with random system positions
                for obj in systems.get(current_system, []):
                    if obj.type == 'star':
                        if not hasattr(obj, 'system_q') or not hasattr(obj, 'system_r'):
                            obj.system_q = random.randint(0, hex_grid.cols - 1)
                            obj.system_r = random.randint(0, hex_grid.rows - 1)
                        px, py = hex_grid.get_hex_center(obj.system_q, obj.system_r)
                        pygame.draw.circle(screen, (255, 255, 0), (int(px), int(py)), 10)
                
                # Animate and draw all planets associated with stars in this system
                planets_in_system = [orbit for orbit in planet_orbits if orbit['star'] == current_system]
                if last_debug_system != current_system:
                    print(f"[DEBUG] System {current_system} has {len(planets_in_system)} planets.")
                    last_debug_system = current_system
                
                for orbit in planets_in_system:
                    # Get star position in system coordinates
                    star_obj = next((obj for obj in systems.get(current_system, []) if obj.type == 'star'), None)
                    if star_obj and hasattr(star_obj, 'system_q') and hasattr(star_obj, 'system_r'):
                        star_px, star_py = hex_grid.get_hex_center(star_obj.system_q, star_obj.system_r)
                    else:
                        star_px, star_py = hex_grid.get_hex_center(current_system[0], current_system[1])
                    
                    hex_size = hex_grid.hex_size if hasattr(hex_grid, 'hex_size') else 20
                    orbit_radius_px = orbit['hex_radius'] * hex_size * 0.85
                    key = (orbit['star'], orbit['planet'])
                    dt = clock.get_time()
                    planet_anim_state[key] += orbit['speed'] * dt
                    angle = planet_anim_state[key]
                    planet_px = star_px + orbit_radius_px * math.cos(angle)
                    planet_py = star_py + orbit_radius_px * math.sin(angle)
                    pygame.draw.circle(screen, (0, 255, 0), (int(planet_px), int(planet_py)), 6)
                
                # Draw other objects (starbase, enemy, anomaly, player) with system positions
                for obj in systems.get(current_system, []):
                    if obj.type != 'star':
                        if not hasattr(obj, 'system_q') or not hasattr(obj, 'system_r'):
                            obj.system_q = random.randint(0, hex_grid.cols - 1)
                            obj.system_r = random.randint(0, hex_grid.rows - 1)
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
                            # Draw moving player ship at animated position if moving, else at logical position
                            if system_ship_moving and system_ship_anim_x is not None and system_ship_anim_y is not None:
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

        # Docked Popup (right side, full height below status bar)
        docked_rect = pygame.Rect(
            WIDTH - DOCKED_POPUP_WIDTH,
            STATUS_HEIGHT,
            DOCKED_POPUP_WIDTH,
            HEIGHT - STATUS_HEIGHT
        )
        pygame.draw.rect(screen, COLOR_DOCKED_POPUP, docked_rect)
        docked_label = font.render('Docked Popup', True, COLOR_TEXT)
        screen.blit(
            docked_label,
            (WIDTH - DOCKED_POPUP_WIDTH + 20, STATUS_HEIGHT + 20)
        )

        # Event Log (bottom left)
        event_rect = pygame.Rect(0, bottom_pane_y, event_log_width, bottom_pane_height)
        pygame.draw.rect(screen, COLOR_EVENT_LOG, event_rect)
        event_label = font.render('Event Log', True, COLOR_TEXT)
        screen.blit(event_label, (20, bottom_pane_y + 20))
        # Draw event log lines with text wrapping
        log_font = pygame.font.SysFont(None, 20)  # Slightly smaller font
        log_area_width = event_log_width - 40  # Account for padding
        y_offset = bottom_pane_y + 50
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
                screen.blit(text_surface, (20, y_offset + rendered_lines * line_height))
                rendered_lines += 1

        # Control Panel (bottom right)
        control_rect = pygame.Rect(event_log_width, bottom_pane_y, 
                                    control_panel_width, bottom_pane_height)
        pygame.draw.rect(screen, COLOR_CONTROL_PANEL, control_rect)
        control_label = font.render('Control Panel', True, COLOR_TEXT)
        screen.blit(control_label, (event_log_width + 20, 
                                     bottom_pane_y + 20))

        # Draw button panel on top of control panel
        button_rects, toggle_btn_rect = draw_button_panel(
            screen,
            event_log_width,
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
                    print(f"Button {clicked_index} clicked")
                    # Scan button is at index 2
                    if clicked_index == 2:
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
                                            'speed': random.uniform(0.00001, 0.00005)  # Much slower speed
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
                                        if (rand_q, rand_r) not in occupied:
                                            player_obj = MapObject('player', current_system[0], current_system[1])
                                            player_obj.system_q = rand_q
                                            player_obj.system_r = rand_r
                                            systems[current_system].append(player_obj)
                                            break
                                    else:
                                        player_obj = MapObject('player', current_system[0], current_system[1])
                                        player_obj.system_q = 0
                                        player_obj.system_r = 0
                                        systems[current_system].append(player_obj)
                                else:
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
                            system_dest_q, system_dest_r = q, r
                            system_ship_moving = True
                            system_move_start_time = pygame.time.get_ticks()
                            # Start position in pixels
                            system_ship_anim_x, system_ship_anim_y = hex_grid.get_hex_center(player_obj.system_q, player_obj.system_r)
                            add_event_log(f"Setting course for system hex ({q}, {r})")
                            print(f"System ship moving to hex ({q}, {r})")

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
                
                # Generate or restore objects for this system even if not scanned
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

        # Update system ship position (delta time based)
        if system_ship_moving and system_dest_q is not None and system_dest_r is not None and map_mode == 'system':
            # Find player object in current system
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