import pygame
import math
import sys
import os
import traceback
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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

# Generate map objects by system (now returns systems, star_coords, lazy_object_coords)
systems, star_coords, lazy_object_coords = place_objects_by_system()

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

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

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

        # --- FOG OF WAR OVERLAY (SECTOR MAP) ---
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
                # Show indicator for any hex with a star or any lazy object
                occupied_hexes = set(star_coords)
                for coords_set in lazy_object_coords.values():
                    occupied_hexes.update(coords_set)
                for q, r in occupied_hexes:
                    px, py = hex_grid.get_hex_center(q, r)
                    pygame.draw.circle(
                        screen, (100, 100, 130), (int(px), int(py)), 6
                    )
                logging.debug(f"[SECTOR] Drawing indicators for {len(occupied_hexes)} occupied hexes.")
        else:
            # In system view, always draw the central star(s)
            for star in [obj for obj in systems.get(current_system, []) if obj.type == 'star']:
                px, py = hex_grid.get_hex_center(star.q, star.r)
                pygame.draw.circle(
                    screen, (255, 255, 0), (int(px), int(py)), 10
                )

            # Draw other objects only if the system has been scanned
            if current_system in scanned_systems:
                # Ensure non-star objects are present (restore or generate)
                if current_system in system_object_states:
                    non_star_objs = [
                        MapObject(d['type'], d['q'], d['r'], **(d.get('props', {})))
                        for d in system_object_states[current_system]
                    ]
                    logging.debug(f"[SYSTEM] Restored non-star objects: {non_star_objs}")
                else:
                    non_star_objs = generate_system_objects(
                        current_system[0], current_system[1], lazy_object_coords
                    )
                    logging.debug(f"[SYSTEM] Generated non-star objects: {non_star_objs}")
                # Draw non-star objects
                for obj in non_star_objs:
                    px, py = hex_grid.get_hex_center(obj.q, obj.r)
                    if obj.type == 'planet':
                        pygame.draw.circle(
                            screen, (0, 255, 0), (int(px), int(py)), 6
                        )
                    elif obj.type == 'starbase':
                        pygame.draw.rect(
                            screen, (0, 0, 255), (int(px)-6, int(py)-6, 12, 12)
                        )
                    elif obj.type == 'enemy':
                        pygame.draw.polygon(
                            screen, (255, 0, 0), [
                                (int(px), int(py)-8),
                                (int(px)-6, int(py)+4),
                                (int(px)+6, int(py)+4)
                            ]
                        )
                    elif obj.type == 'anomaly':
                        pygame.draw.circle(
                            screen, (255, 0, 255), (int(px), int(py)), 5
                        )
                    elif obj.type == 'player':
                        pygame.draw.circle(
                            screen, (0, 255, 255), (int(px), int(py)), 8
                        )

        # Draw player ship
        if map_mode == 'sector':
            pygame.draw.circle(
                screen, (0, 255, 255), (int(ship_anim_x), int(ship_anim_y)), 8
            )
        else:
            player_in_system = next(
                (obj for obj in systems.get(current_system, []) if obj.type == 'player'),
                None
            )
            if player_in_system:
                px, py = hex_grid.get_hex_center(player_in_system.q, player_in_system.r)
                pygame.draw.circle(
                    screen, (0, 255, 255), (int(px), int(py)), 8
                )

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
                            print("Sector scan active. All systems revealed.")
                        elif map_mode == 'system':
                            if current_system not in scanned_systems:
                                scanned_systems.add(current_system)
                                # Store non-star objects for this system for persistence (as dicts)
                                non_star_objs = generate_system_objects(
                                    current_system[0], current_system[1], lazy_object_coords
                                )
                                system_object_states[current_system] = [
                                    {
                                        'type': obj.type,
                                        'q': obj.q,
                                        'r': obj.r,
                                        'props': obj.props
                                    } for obj in non_star_objs
                                ]
                                print(f"System at {current_system} scanned. Objects revealed and state saved.")
                            else:
                                print(f"System at {current_system} was already scanned.")

                if toggle_clicked:
                    print("Toggle button clicked")
                    map_mode = 'system' if map_mode == 'sector' else 'sector'

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
                        print(f"Ship moving to hex ({q}, {r})")

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
                # Check if there's a system here (star or any lazy object)
                system_here = (
                    (ship_q, ship_r) in star_coords or
                    any((ship_q, ship_r) in coords_set for coords_set in lazy_object_coords.values())
                )
                if system_here:
                    logging.info(f"[MOVE] Entering system at ({ship_q}, {ship_r})")
                    map_mode = 'system'
                    current_system = (ship_q, ship_r)
                    if current_system in scanned_systems and current_system in system_object_states:
                        # Restore non-star objects for this system
                        pass  # Already handled in draw logic

        # Draw destination indicator (red circle)
        if ship_moving and dest_q is not None and dest_r is not None and map_mode == 'sector':
            dest_x, dest_y = hex_grid.get_hex_center(dest_q, dest_r)
            pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)

        # --- FOG OF WAR OVERLAY (SYSTEM MAP) ---
        if map_mode == 'system' and current_system not in scanned_systems:
            for row in range(hex_grid.rows):
                for col in range(hex_grid.cols):
                    cx, cy = hex_grid.get_hex_center(col, row)
                    hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=153)

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