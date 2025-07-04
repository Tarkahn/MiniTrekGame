import pygame
import math

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

def hex_corner(center, radius, i):
    angle_deg = 60 * i - 30
    angle_rad = math.radians(angle_deg)
    return (
        center[0] + radius * math.cos(angle_rad),
        center[1] + radius * math.sin(angle_rad)
    )


def draw_hex(surface, center, radius, color, outline):
    points = [hex_corner(center, radius, i) for i in range(6)]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, outline, points, 1)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

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

    # Debug: Draw red rectangle around map pane
    pygame.draw.rect(screen, COLOR_MAP_DEBUG, map_rect, 2)

    # Debug: Draw green rectangle around grid bounding box
    grid_rect = pygame.Rect(
        int(grid_x_offset), int(grid_y_offset),
        int(grid_width), int(grid_height)
    )
    pygame.draw.rect(screen, COLOR_GRID_DEBUG, grid_rect, 2)

    # Draw hex grid inside map area (no gaps)
    for row in range(HEX_ROWS):
        for col in range(HEX_COLS):
            x = grid_x_offset + hex_width * (col + 0.5 * (row % 2))
            y = grid_y_offset + vert_spacing * row + hex_radius
            draw_hex(screen, (x, y), hex_radius, HEX_BG, HEX_OUTLINE)

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

    pygame.display.flip()

pygame.quit() 