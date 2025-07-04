import pygame
import math
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from galaxy_generation.object_placement import place_objects_by_system
from ui.hex_map import draw_hex_grid, hex_to_pixel
from ui.button_panel import draw_button_panel
import traceback

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

# Hex grid constants
HEX_ROWS = 20
HEX_COLS = 20
# For pointy-topped hexes:
# width = sqrt(3) * r, height = 2 * r
# horizontal spacing = width, vertical spacing = 3/4 * height
# Calculate the largest possible radius so the grid fits exactly
hex_radius_x = map_size / (math.sqrt(3) * (HEX_COLS + 0.5))
hex_radius_y = map_size / (1 + 0.75 * (HEX_ROWS - 1)) / 2
hex_radius = min(hex_radius_x, hex_radius_y)
hex_width = math.sqrt(3) * hex_radius
hex_height = 2 * hex_radius
vert_spacing = 0.75 * hex_height
# Calculate grid offset to center in map area
grid_width = hex_width * HEX_COLS
grid_height = vert_spacing * (HEX_ROWS - 1) + hex_height
grid_x_offset = map_x + (map_size - grid_width) / 2  # center in pane
grid_y_offset = map_y + (map_size - grid_height) / 2

# Generate map objects by system
systems, current_system, all_objects = place_objects_by_system()

# Map mode state
map_mode = 'sector'  # or 'system'

# Button panel parameters
BUTTON_W, BUTTON_H = 120, 40
BUTTON_GAP = 20
TOGGLE_BTN_W, TOGGLE_BTN_H = 200, 40
TOGGLE_BTN_Y = bottom_pane_y + 30 + 4 * (BUTTON_H + BUTTON_GAP)
BUTTON_COLOR = (100, 100, 180)

# Button state tracking
button_pressed = [False, False, False, False]
toggle_btn_pressed = [False]  # Use list for mutability in handler

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

        # Debug: Draw red rectangle around map pane
        pygame.draw.rect(screen, COLOR_MAP_DEBUG, map_rect, 2)

        # Debug: Draw green rectangle around grid bounding box
        grid_rect = pygame.Rect(
            int(grid_x_offset), int(grid_y_offset),
            int(grid_width), int(grid_height)
        )
        pygame.draw.rect(screen, COLOR_GRID_DEBUG, grid_rect, 2)

        # Draw hex grid inside map area (no gaps)
        draw_hex_grid(
            screen, HEX_ROWS, HEX_COLS, grid_x_offset, grid_y_offset,
            hex_width, vert_spacing, hex_radius, HEX_BG, HEX_OUTLINE,
            highlight=current_system if map_mode == 'sector' else None
        )

        if map_mode == 'sector':
            for (q, r), objs in systems.items():
                if objs:
                    px, py = hex_to_pixel(
                        q, r, grid_x_offset, grid_y_offset, hex_width, vert_spacing, hex_radius
                    )
                    pygame.draw.circle(screen, (180, 180, 180), (px, py), 6)
        else:
            for obj in systems.get(current_system, []):
                px, py = hex_to_pixel(
                    obj.q, obj.r, grid_x_offset, grid_y_offset, hex_width, vert_spacing, hex_radius
                )
                if obj.type == 'star':
                    pygame.draw.circle(screen, (255, 230, 40), (px, py), 14)
                elif obj.type == 'planet':
                    pygame.draw.circle(screen, (60, 120, 255), (px, py), 12)
                elif obj.type == 'starbase':
                    rect = pygame.Rect(
                        px - 10, py - 10, 20, 20
                    )
                    pygame.draw.rect(screen, (180, 180, 180), rect)
                elif obj.type == 'enemy':
                    points = [
                        (px, py - 14),
                        (px - 12, py + 10),
                        (px + 12, py + 10)
                    ]
                    pygame.draw.polygon(screen, (255, 80, 80), points)
                elif obj.type == 'anomaly':
                    points = [
                        (px, py - 12),
                        (px - 12, py),
                        (px, py + 12),
                        (px + 12, py)
                    ]
                    pygame.draw.polygon(screen, (180, 80, 255), points)
                elif obj.type == 'player':
                    pygame.draw.circle(screen, (0, 220, 255), (px, py), 15)
                    pygame.draw.circle(screen, (255, 255, 255), (px, py), 15, 2)

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

        # Event Log (bottom left, half the map width)
        event_log_rect = pygame.Rect(
            0, bottom_pane_y, event_log_width, bottom_pane_height)
        pygame.draw.rect(screen, COLOR_EVENT_LOG, event_log_rect)
        event_log_label = font.render('Event Log', True, COLOR_TEXT)
        screen.blit(
            event_log_label,
            (20, bottom_pane_y + 20)
        )

        # --- PLACEHOLDER EVENT LOG ENTRIES ---
        for i, log in enumerate([
            "[INFO] Game started.",
            "[EVENT] Ship moved to (10, 10)",
            "[ALERT] Enemy detected!"
        ]):
            lx = 20
            ly = bottom_pane_y + 30 + i * 32
            log_label = font.render(log, True, (220, 220, 180))
            screen.blit(log_label, (lx, ly))

        # Control Panel (bottom right, half the map width)
        control_panel_rect = pygame.Rect(
            event_log_width, bottom_pane_y,
            control_panel_width, bottom_pane_height)
        pygame.draw.rect(screen, COLOR_CONTROL_PANEL, control_panel_rect)
        control_panel_label = font.render('Control Panel', True, COLOR_TEXT)
        screen.blit(
            control_panel_label,
            (event_log_width + 20, bottom_pane_y + 20)
        )
        # Draw the button panel LAST so buttons are on top
        button_rects, toggle_btn_rect = draw_button_panel(
            screen, event_log_width, bottom_pane_y, BUTTON_W, BUTTON_H, BUTTON_GAP,
            font, BUTTON_COLOR, COLOR_TEXT, map_mode, TOGGLE_BTN_W, TOGGLE_BTN_H,
            TOGGLE_BTN_Y
        )

        # Event handling (moved here for clarity)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Only handle button events if button_rects and toggle_btn_rect exist
            if button_rects and toggle_btn_rect:
                from ui.button_panel import handle_button_events
                button_pressed, toggle_btn_pressed, clicked_index, toggle_clicked = handle_button_events(
                    event, button_rects, toggle_btn_rect, button_pressed, toggle_btn_pressed
                )
                if clicked_index is not None:
                    print(f"Button {clicked_index} clicked")
                if toggle_clicked:
                    print("Toggle button clicked")
                    map_mode = 'system' if map_mode == 'sector' else 'sector'

        pygame.display.flip()
    pygame.quit()
except Exception as e:
    print("\n--- GAME CRASHED ---")
    traceback.print_exc()
    pygame.quit() 