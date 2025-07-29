"""
Enemy Scan Panel - Dedicated panel for displaying enemy scan results
LCARS-style panel that shows detailed information about scanned enemies
"""

import pygame
import math

class EnemyScanPanel:
    """
    LCARS-style enemy scan panel showing:
    - Scanned enemy details
    - Distance and bearing
    - Shield/hull status
    - Weapon systems
    - Threat assessment
    """
    
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.small_font = pygame.font.Font(None, 16)
        self.large_font = pygame.font.Font(None, 22)
        
        # LCARS Colors - Enemy themed (red/orange)
        self.bg_color = (40, 20, 20)        # Dark red background
        self.border_color = (255, 102, 102)  # LCARS red
        self.text_color = (255, 255, 255)    # White text
        self.enemy_color = (255, 80, 80)     # Enemy red
        self.warning_color = (255, 255, 0)   # Yellow warning
        self.critical_color = (255, 40, 40)  # Critical red
        self.good_color = (80, 255, 80)      # Green for low threat
        self.bar_bg_color = (80, 40, 40)     # Dark bar background
        
        # Scan data storage
        self.scanned_enemies = {}  # Dictionary of enemy_id -> scan_data
        self.selected_enemy_id = None
        
    def add_scan_result(self, enemy_id, enemy_data):
        """Add or update scan results for an enemy."""
        self.scanned_enemies[enemy_id] = {
            'name': enemy_data.get('name', f'Unknown Vessel {enemy_id}'),
            'position': enemy_data.get('position', (0, 0)),
            'hull': enemy_data.get('hull', 100),
            'max_hull': enemy_data.get('max_hull', 100),
            'shields': enemy_data.get('shields', 0),
            'max_shields': enemy_data.get('max_shields', 100),
            'energy': enemy_data.get('energy', 100),
            'max_energy': enemy_data.get('max_energy', 100),
            'weapons': enemy_data.get('weapons', []),
            'distance': enemy_data.get('distance', 0),
            'bearing': enemy_data.get('bearing', 0),
            'threat_level': enemy_data.get('threat_level', 'Unknown'),
            'system_integrity': enemy_data.get('system_integrity', {}),
            'power_allocation': enemy_data.get('power_allocation', {}),
            'weapons_status': enemy_data.get('weapons_status', 'Unknown'),
            'engine_status': enemy_data.get('engine_status', 'Unknown'),
            'scan_time': pygame.time.get_ticks()
        }
        
        # Auto-select if this is the first or only enemy
        if len(self.scanned_enemies) == 1:
            self.selected_enemy_id = enemy_id
    
    def clear_scans(self):
        """Clear all scan results."""
        self.scanned_enemies.clear()
        self.selected_enemy_id = None
    
    def remove_scan_result(self, enemy_id):
        """Remove scan results for a specific enemy."""
        if enemy_id in self.scanned_enemies:
            del self.scanned_enemies[enemy_id]
            # If this was the selected enemy, clear selection or select another
            if self.selected_enemy_id == enemy_id:
                if self.scanned_enemies:
                    # Select the first remaining enemy
                    self.selected_enemy_id = next(iter(self.scanned_enemies.keys()))
                else:
                    # No enemies left
                    self.selected_enemy_id = None
    
    def select_enemy(self, enemy_id):
        """Select an enemy to display details."""
        if enemy_id in self.scanned_enemies:
            self.selected_enemy_id = enemy_id
    
    def draw(self, screen):
        """Draw the enemy scan panel."""
        # Background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Title
        title_text = self.large_font.render("ENEMY SCAN", True, self.border_color)
        screen.blit(title_text, (self.rect.x + 10, self.rect.y + 5))
        
        current_y = self.rect.y + 35
        
        if not self.scanned_enemies:
            # No scan data
            no_data_text = self.font.render("No enemies scanned", True, self.text_color)
            screen.blit(no_data_text, (self.rect.x + 10, current_y))
            
            instruction_text = self.small_font.render("Right-click enemies to scan", True, (150, 150, 150))
            screen.blit(instruction_text, (self.rect.x + 10, current_y + 30))
            
        else:
            # Enemy selector (if multiple enemies)
            if len(self.scanned_enemies) > 1:
                current_y = self.draw_enemy_selector(screen, current_y)
                current_y += 10
            
            # Selected enemy details
            if self.selected_enemy_id and self.selected_enemy_id in self.scanned_enemies:
                current_y = self.draw_enemy_details(screen, current_y)
    
    def draw_enemy_selector(self, screen, y):
        """Draw enemy selection buttons if multiple enemies scanned."""
        selector_label = self.small_font.render("CONTACTS:", True, self.border_color)
        screen.blit(selector_label, (self.rect.x + 10, y))
        y += 20
        
        button_width = 30
        button_height = 20
        button_spacing = 35
        x = self.rect.x + 10
        
        for i, enemy_id in enumerate(self.scanned_enemies.keys()):
            # Enemy button
            button_rect = pygame.Rect(x, y, button_width, button_height)
            
            # Color based on selection
            if enemy_id == self.selected_enemy_id:
                button_color = self.enemy_color
                text_color = (255, 255, 255)
            else:
                button_color = self.bar_bg_color
                text_color = (200, 200, 200)
            
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, self.border_color, button_rect, 1)
            
            # Enemy number
            enemy_num = str(i + 1)
            num_text = self.small_font.render(enemy_num, True, text_color)
            text_rect = num_text.get_rect(center=button_rect.center)
            screen.blit(num_text, text_rect)
            
            x += button_spacing
        
        return y + 30
    
    def draw_enemy_details(self, screen, y):
        """Draw detailed information about the selected enemy."""
        enemy_data = self.scanned_enemies[self.selected_enemy_id]
        
        # Enemy name
        name_text = self.font.render(enemy_data['name'], True, self.enemy_color)
        screen.blit(name_text, (self.rect.x + 10, y))
        y += 25
        
        # Position and distance
        distance = enemy_data['distance']
        bearing = enemy_data['bearing']
        
        pos_text = f"Range: {distance:.1f} km"
        pos_surface = self.small_font.render(pos_text, True, self.text_color)
        screen.blit(pos_surface, (self.rect.x + 10, y))
        y += 18
        
        bearing_text = f"Bearing: {bearing:.0f}°"
        bearing_surface = self.small_font.render(bearing_text, True, self.text_color)
        screen.blit(bearing_surface, (self.rect.x + 10, y))
        y += 25
        
        # Hull status
        y = self.draw_status_bar(screen, y, "HULL", 
                                 enemy_data['hull'], enemy_data['max_hull'])
        
        # Shield status
        y = self.draw_status_bar(screen, y, "SHIELDS", 
                                 enemy_data['shields'], enemy_data['max_shields'])
        
        # Energy status
        y = self.draw_status_bar(screen, y, "ENERGY", 
                                 enemy_data['energy'], enemy_data['max_energy'])
        
        # Threat assessment
        y += 10
        threat_label = self.small_font.render("THREAT LEVEL:", True, self.border_color)
        screen.blit(threat_label, (self.rect.x + 10, y))
        y += 18
        
        threat_level = enemy_data['threat_level']
        if threat_level == 'Critical':
            threat_color = self.critical_color
        elif threat_level == 'High':
            threat_color = self.enemy_color
        elif threat_level == 'Medium':
            threat_color = self.warning_color
        else:
            threat_color = self.good_color
        
        threat_text = self.font.render(threat_level, True, threat_color)
        screen.blit(threat_text, (self.rect.x + 10, y))
        y += 30
        
        # Weapons (if any)
        if enemy_data['weapons']:
            weapons_label = self.small_font.render("WEAPONS:", True, self.border_color)
            screen.blit(weapons_label, (self.rect.x + 10, y))
            y += 18
            
            for weapon in enemy_data['weapons']:
                weapon_text = f"• {weapon}"
                weapon_surface = self.small_font.render(weapon_text, True, self.text_color)
                screen.blit(weapon_surface, (self.rect.x + 15, y))
                y += 16
        
        # Scan age
        y += 10
        scan_age = (pygame.time.get_ticks() - enemy_data['scan_time']) / 1000.0
        age_text = f"Scan age: {scan_age:.1f}s"
        age_surface = self.small_font.render(age_text, True, (150, 150, 150))
        screen.blit(age_surface, (self.rect.x + 10, y))
        
        return y + 20
    
    def draw_status_bar(self, screen, y, label, current, maximum):
        """Draw a status bar for hull/shields/energy."""
        # Label
        label_surface = self.small_font.render(f"{label}:", True, self.border_color)
        screen.blit(label_surface, (self.rect.x + 10, y))
        
        # Status bar
        bar_width = self.rect.width - 80
        bar_height = 12
        bar_x = self.rect.x + 10
        bar_y = y + 16
        
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, self.bar_bg_color, bar_rect)
        
        # Fill based on current/max ratio
        if maximum > 0:
            fill_ratio = current / maximum
            fill_width = int(bar_width * fill_ratio)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            
            # Color based on status level
            if fill_ratio > 0.6:
                color = self.good_color
            elif fill_ratio > 0.3:
                color = self.warning_color
            else:
                color = self.critical_color
            
            pygame.draw.rect(screen, color, fill_rect)
        
        pygame.draw.rect(screen, self.border_color, bar_rect, 1)
        
        # Status text
        status_text = f"{int(current)}/{int(maximum)}"
        status_surface = self.small_font.render(status_text, True, self.text_color)
        screen.blit(status_surface, (self.rect.x + bar_width + 15, y + 14))
        
        return y + 35
    
    def handle_click(self, pos):
        """Handle mouse clicks on the panel (for enemy selection)."""
        if not self.rect.collidepoint(pos):
            return None
        
        if len(self.scanned_enemies) <= 1:
            return None
        
        # Check if click is in enemy selector area
        selector_y = self.rect.y + 55  # Approximate selector position
        if selector_y <= pos[1] <= selector_y + 20:
            # Calculate which enemy button was clicked
            relative_x = pos[0] - (self.rect.x + 10)
            button_index = relative_x // 35  # 35 = button spacing
            
            enemy_ids = list(self.scanned_enemies.keys())
            if 0 <= button_index < len(enemy_ids):
                self.select_enemy(enemy_ids[button_index])
                return enemy_ids[button_index]
        
        return None

def create_enemy_scan_panel(x, y, width, height, font):
    """Factory function to create an enemy scan panel."""
    return EnemyScanPanel(x, y, width, height, font)