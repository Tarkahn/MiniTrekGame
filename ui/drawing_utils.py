"""
Drawing and rendering utilities for the Star Trek Tactical Game
"""
import pygame
import math
import random
from ui.ui_config import *
from ui.text_utils import wrap_text


def get_star_color():
    """Generate realistic star colors based on stellar classification."""
    star_colors = [
        (255, 255, 255),  # White (white dwarf, hot stars)
        (255, 254, 250),  # Blue-white
        (255, 244, 234),  # Yellow-white
        (255, 229, 206),  # Yellow (G-type like our Sun)
        (255, 204, 111),  # Orange
        (255, 178, 102),  # Orange-red
        (255, 154, 86),   # Red-orange
        (255, 128, 74),   # Red (M-type red dwarf)
    ]
    return random.choice(star_colors)


def get_planet_color():
    """Generate varied planet colors."""
    planet_colors = [
        (100, 149, 237),  # Cornflower blue (Earth-like)
        (255, 228, 181),  # Moccasin (desert world)
        (189, 183, 107),  # Dark khaki (rocky)
        (70, 130, 180),   # Steel blue (ice world)
        (244, 164, 96),   # Sandy brown (Mars-like)
        (176, 196, 222),  # Light steel blue (gas giant)
        (147, 112, 219),  # Medium purple (exotic)
        (188, 143, 143),  # Rosy brown
    ]
    return random.choice(planet_colors)


def draw_enemy_popup(screen, popup_info):
    """Draw an enemy popup window with ship stats."""
    # Extract info
    rect = popup_info['rect']
    enemy = popup_info['enemy_obj']
    visible = popup_info.get('visible', True)
    enemy_id = popup_info.get('enemy_id', 'Unknown')
    selected = popup_info.get('selected', False)
    
    if not visible:
        return
        
    # Window background
    pygame.draw.rect(screen, (40, 40, 60), rect)
    
    # Border - highlight if selected
    border_color = (255, 255, 0) if selected else (100, 100, 150)
    border_width = 3 if selected else 2
    pygame.draw.rect(screen, border_color, rect, border_width)
    
    # Title bar
    title_rect = pygame.Rect(rect.x, rect.y, rect.width, 30)
    pygame.draw.rect(screen, (60, 60, 90), title_rect)
    pygame.draw.line(screen, (100, 100, 150), (rect.x, rect.y + 30), (rect.x + rect.width, rect.y + 30), 2)
    
    # Title text
    title_text = popup_info['title_font'].render(f"Enemy Ship {enemy_id}", True, (220, 220, 220))
    screen.blit(title_text, (rect.x + 10, rect.y + 5))
    
    # Close button
    close_rect = pygame.Rect(rect.x + rect.width - 25, rect.y + 5, 20, 20)
    pygame.draw.rect(screen, (150, 50, 50), close_rect)
    pygame.draw.line(screen, (220, 220, 220), (close_rect.x + 5, close_rect.y + 5), 
                     (close_rect.x + 15, close_rect.y + 15), 2)
    pygame.draw.line(screen, (220, 220, 220), (close_rect.x + 15, close_rect.y + 5), 
                     (close_rect.x + 5, close_rect.y + 15), 2)
    popup_info['close_rect'] = close_rect
    
    # Stats display
    y_offset = rect.y + 40
    line_height = 25
    
    # Get enemy stats with defaults
    health = getattr(enemy, 'health', 100)
    max_health = getattr(enemy, 'max_health', 100)
    shields = getattr(enemy, 'shields', 100)
    max_shields = getattr(enemy, 'max_shields', 100)
    energy = getattr(enemy, 'energy', 1000)
    max_energy = getattr(enemy, 'max_energy', 1000)
    weapons_status = getattr(enemy, 'weapons_status', 'Online')
    engine_status = getattr(enemy, 'engine_status', 'Online')
    distance = getattr(enemy, 'distance', 0.0)
    bearing = getattr(enemy, 'bearing', 0.0)
    
    # Stats to display
    stats = [
        ("Hull:", f"{health}/{max_health}", health / max_health if max_health > 0 else 0),
        ("Shields:", f"{shields}/{max_shields}", shields / max_shields if max_shields > 0 else 0),
        ("Energy:", f"{energy}/{max_energy}", energy / max_energy if max_energy > 0 else 0),
        ("Weapons:", weapons_status, None),
        ("Engines:", engine_status, None),
        ("Distance:", f"{distance:.1f} units", None),
        ("Bearing:", f"{bearing:.0f}°", None)
    ]
    
    font = popup_info['font']
    small_font = popup_info['small_font']
    
    for label, value, ratio in stats:
        # Label
        label_surface = font.render(label, True, (180, 180, 180))
        screen.blit(label_surface, (rect.x + 10, y_offset))
        
        # Value
        value_color = (220, 220, 220)
        if ratio is not None:
            # Color code based on ratio
            if ratio > 0.66:
                value_color = (100, 255, 100)
            elif ratio > 0.33:
                value_color = (255, 255, 100)
            else:
                value_color = (255, 100, 100)
                
            # Draw bar
            bar_x = rect.x + 90
            bar_y = y_offset + 5
            bar_width = 120
            bar_height = 15
            
            # Background
            pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
            # Fill
            fill_width = int(bar_width * ratio)
            if fill_width > 0:
                pygame.draw.rect(screen, value_color, (bar_x, bar_y, fill_width, bar_height))
            # Border
            pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height), 1)
            
            # Text overlay
            value_surface = small_font.render(value, True, (220, 220, 220))
            text_rect = value_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
            screen.blit(value_surface, text_rect)
        else:
            # Just text
            value_surface = font.render(value, True, value_color)
            screen.blit(value_surface, (rect.x + 90, y_offset))
        
        y_offset += line_height
        
    # Target indicator if selected
    if selected:
        target_text = font.render("[TARGETED]", True, (255, 255, 0))
        text_rect = target_text.get_rect(center=(rect.x + rect.width // 2, rect.y + rect.height - 20))
        screen.blit(target_text, text_rect)


def draw_event_log(screen, event_log_manager, x, y, width, height, font):
    """Draw the event log panel."""
    # Event Log Panel
    event_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, COLOR_EVENT_LOG, event_rect)
    pygame.draw.rect(screen, COLOR_EVENT_LOG_BORDER, event_rect, 2)
    event_label = font.render('Event Log', True, COLOR_TEXT)
    screen.blit(event_label, (x + 20, y + 10))
    
    # Render log entries
    log_font = font
    log_area_width = width - 40  # Account for padding
    y_offset = y + 50  # Account for Event Log label
    line_height = 20  # Tighter line spacing
    
    # Process and render each log entry with wrapping
    rendered_lines = 0
    for line in event_log_manager.get_recent_messages(EVENT_LOG_MAX_LINES):
        if rendered_lines >= EVENT_LOG_MAX_LINES:
            break
        
        wrapped_lines = wrap_text(line, log_area_width, log_font)
        for wrapped_line in wrapped_lines:
            if rendered_lines >= EVENT_LOG_MAX_LINES:
                break
            text_surface = log_font.render(wrapped_line, True, COLOR_TEXT)
            screen.blit(text_surface, (x + 20, y_offset + rendered_lines * line_height))
            rendered_lines += 1


def draw_phaser_animation(screen, start_pos, end_pos, progress, now):
    """Draw animated phaser beam."""
    if progress < 0 or progress > 1:
        return
        
    # Interpolate position along the line
    px1, py1 = start_pos
    px2, py2 = end_pos
    
    # Draw a thick laser line (yellow/red)
    color = (255, 255, 0) if (now // 100) % 2 == 0 else (255, 0, 0)
    pygame.draw.line(screen, color, (int(px1), int(py1)), (int(px2), int(py2)), 4)