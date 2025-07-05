import pygame
import math
import sys
import os
import traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from galaxy_generation.object_placement import place_objects_by_system
from ui.hex_map import create_hex_grid_for_map
from ui.button_panel import draw_button_panel, handle_button_events

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

# Generate map objects by system
systems, current_system, all_objects = place_objects_by_system()

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

# --- Ship navigation state ---
# Find initial player position (sector coordinates)
player_obj = next((obj for obj in all_objects if obj.type == 'player'), None)
if player_obj:
    ship_q, ship_r = player_obj.q, player_obj.r
else:
    ship_q, ship_r = 0, 0  # fallback

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

try:
    running = True
    while running:
        screen.fill(COLOR_BG)
        # Status/Tooltip Panel (top)
        status_rect = pygame.Rect(0, 0, WIDTH, STATUS_HEIGHT)
        pygame.draw.rect(screen, COLOR_STATUS, status_rect)
        status_label = font.render('Status/Tooltip Panel', True, COLOR_TEXT)
        screen.blit(status_label, (10, 8))

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

        # Draw objects on the grid
        if map_mode == 'sector':
            # Only draw system indicators if a sector scan has been done
            if sector_scan_active:
                occupied_hexes = {(obj.q, obj.r) for obj in all_objects}
                for q, r in occupied_hexes:
                    px, py = hex_grid.get_hex_center(q, r)
                    # Use a subtle color for scanned system locations
                    pygame.draw.circle(screen, (100, 100, 130),
                                       (int(px), int(py)), 6)
        else:
            # In system view, always draw the central star
            star = next((obj for obj in systems.get(current_system, [])
                         if obj.type == 'star'), None)
            if star:
                px, py = hex_grid.get_hex_center(star.q, star.r)
                pygame.draw.circle(screen, (255, 255, 0), (int(px), int(py)), 10)

            # Draw other objects only if the system has been scanned
            if current_system in scanned_systems:
                for obj in systems.get(current_system, []):
                    if obj.type == 'star':
                        continue  # Already drawn
                    px, py = hex_grid.get_hex_center(obj.q, obj.r)
                    if obj.type == 'planet':
                        pygame.draw.circle(
                            screen, (0, 255, 0), (int(px), int(py)), 6)
                    elif obj.type == 'starbase':
                        pygame.draw.rect(
                            screen, (0, 0, 255), (int(px)-6, int(py)-6, 12, 12))
                    elif obj.type == 'enemy':
                        pygame.draw.polygon(screen, (255, 0, 0), [
                            (int(px), int(py)-8),
                            (int(px)-6, int(py)+4),
                            (int(px)+6, int(py)+4)
                        ])
                    elif obj.type == 'anomaly':
                        pygame.draw.circle(
                            screen, (255, 0, 255), (int(px), int(py)), 5)

        # Draw player ship
        if map_mode == 'sector':
            pygame.draw.circle(screen, (0, 255, 255), (int(ship_anim_x), int(ship_anim_y)), 8)
        else:
            player_in_system = next((obj for obj in systems.get(current_system, []) if obj.type == 'player'), None)
            if player_in_system:
                px, py = hex_grid.get_hex_center(player_in_system.q, player_in_system.r)
                pygame.draw.circle(screen, (0, 255, 255), (int(px), int(py)), 8)

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
                                print(f"System at {current_system} scanned. Objects revealed.")
                            else:
                                print(f"System at {current_system} was already scanned.")

                if toggle_clicked:
                    print("Toggle button clicked")
                    map_mode = 'system' if map_mode == 'sector' else 'sector'

            # Then handle map click events
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Check if click is in map area
                if map_rect.collidepoint(mx, my) and map_mode == 'sector':
                    # Convert to hex coordinates
                    q, r = hex_grid.pixel_to_hex(mx, my)
                    if q is not None and r is not None:
                        # Set new destination
                        dest_q, dest_r = q, r
                        ship_moving = True
                        dest_x, dest_y = hex_grid.get_hex_center(dest_q, dest_r)
                        dx = dest_x - ship_anim_x
                        dy = dest_y - ship_anim_y
                        distance = math.hypot(dx, dy)
                        move_ship_speed = distance / move_frames
                        print(f"Ship moving to hex ({q}, {r})")

        # Update ship position
        if ship_moving and dest_q is not None and dest_r is not None:
            dest_x, dest_y = hex_grid.get_hex_center(dest_q, dest_r)
            dx = dest_x - ship_anim_x
            dy = dest_y - ship_anim_y
            distance = math.hypot(dx, dy)
            
            if distance < move_ship_speed:
                # Arrived at destination
                ship_anim_x, ship_anim_y = dest_x, dest_y
                ship_q, ship_r = dest_q, dest_r
                ship_moving = False
                print(f"Ship arrived at ({ship_q}, {ship_r})")
                
                # Check if there's a system here
                system_here = any(obj.q == ship_q and obj.r == ship_r for obj in all_objects)
                if system_here:
                    # Switch to system map
                    map_mode = 'system'
                    current_system = (ship_q, ship_r)
                    print(f"Entering system at ({ship_q}, {ship_r})")
            else:
                # Move toward destination
                ship_anim_x += move_ship_speed * dx / distance
                ship_anim_y += move_ship_speed * dy / distance

        # Draw destination indicator (red circle)
        if ship_moving and dest_q is not None and dest_r is not None and map_mode == 'sector':
            dest_x, dest_y = hex_grid.get_hex_center(dest_q, dest_r)
            pygame.draw.circle(screen, (255, 0, 0), (int(dest_x), int(dest_y)), 8)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

except Exception as e:
    print("--- GAME CRASHED ---")
    traceback.print_exc()
    print(f"Error: {e}")
finally:
    pygame.quit()
    sys.exit() 