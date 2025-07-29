"""
Rendering utilities for the Star Trek Tactical Game
"""
import pygame
import random
import logging
from ui.ui_config import *
from ui.drawing_utils import get_star_color, get_planet_color
from ui.hex_utils import get_star_hexes, get_planet_hexes


def draw_status_panel(screen, font, label_font, stardate_system):
    """Draw the top status/tooltip panel."""
    status_rect = pygame.Rect(0, 0, WIDTH, STATUS_HEIGHT)
    pygame.draw.rect(screen, COLOR_STATUS, status_rect)
    status_label = label_font.render('Status/Tooltip Panel', True, COLOR_TEXT)
    screen.blit(status_label, (10, 8))
    # Stardate Display
    stardate_label = font.render(stardate_system.format_stardate(), True, COLOR_TEXT)
    screen.blit(stardate_label, (WIDTH - 180, 8))


def draw_map_background(screen, map_x, map_y, map_size, background_loader):
    """Draw the map background and border."""
    map_rect = pygame.Rect(map_x, map_y, map_size, map_size)
    pygame.draw.rect(screen, COLOR_MAP, map_rect)
    
    # Draw background image (lowest layer)
    background_img = background_loader.get_scaled_background(map_size, map_size)
    if background_img:
        screen.blit(background_img, (map_x, map_y))


def draw_system_stars(screen, systems, current_system, hex_grid, background_loader):
    """Draw stars in system view."""
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
                
                # Get or assign star image
                if not hasattr(obj, 'star_image'):
                    obj.star_image = background_loader.get_random_star_image()
                    obj.scaled_star_image = None
                
                # Draw star image if available, otherwise fallback to circle
                if obj.star_image:
                    # Scale image if not already done
                    if obj.scaled_star_image is None:
                        obj.scaled_star_image = background_loader.scale_star_image(
                            obj.star_image, hex_grid.radius * 3.6
                        )
                    
                    if obj.scaled_star_image:
                        # Center the image
                        image_rect = obj.scaled_star_image.get_rect()
                        image_rect.center = (int(center_x), int(center_y))
                        screen.blit(obj.scaled_star_image, image_rect)
                    else:
                        # Fallback to circle if image scaling failed
                        if not hasattr(obj, 'color'):
                            obj.color = get_star_color()
                        pygame.draw.circle(screen, obj.color, 
                                         (int(center_x), int(center_y)), 
                                         int(hex_grid.radius * 3.6))
                else:
                    # Fallback to circle if no image available
                    if not hasattr(obj, 'color'):
                        obj.color = get_star_color()
                    pygame.draw.circle(screen, obj.color, 
                                     (int(center_x), int(center_y)), 
                                     int(hex_grid.radius * 3.6))


def draw_fog_of_war(screen, hex_grid, scanned_systems):
    """Draw fog of war overlay for unscanned systems."""
    for row in range(hex_grid.rows):
        for col in range(hex_grid.cols):
            if (col, row) not in scanned_systems:
                cx, cy = hex_grid.get_hex_center(col, row)
                hex_grid.draw_fog_hex(screen, cx, cy, color=(200, 200, 200), alpha=153)


def draw_sector_indicators(screen, hex_grid, star_coords, lazy_object_coords):
    """Draw indicators for occupied hexes in sector view."""
    occupied_hexes = set(star_coords)
    for coords_set in lazy_object_coords.values():
        occupied_hexes.update(coords_set)
    
    for q, r in occupied_hexes:
        px, py = hex_grid.get_hex_center(q, r)
        pygame.draw.circle(screen, (100, 100, 130), (int(px), int(py)), 6)
    
    logging.debug(f"[SECTOR] Drawing indicators for {len(occupied_hexes)} occupied hexes.")