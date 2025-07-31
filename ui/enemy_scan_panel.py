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
    
    def draw(self, screen, targeted_enemy_id=None):
        """Draw the enemy scan panel showing all scanned enemies simultaneously."""
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
            # Draw all scanned enemies
            for i, (enemy_id, enemy_data) in enumerate(self.scanned_enemies.items()):
                # Check if this enemy is currently targeted
                is_targeted = (targeted_enemy_id == enemy_id)
                current_y = self.draw_enemy_details(screen, current_y, enemy_data, is_targeted, i + 1)
                current_y += 10  # Spacing between enemies
    
    
    def draw_enemy_details(self, screen, y, enemy_data, is_targeted=False, enemy_number=1):
        """Draw detailed information about an enemy."""
        start_y = y
        
        # Enemy name with number
        name_text = f"{enemy_number}. {enemy_data['name']}"
        if is_targeted:
            name_color = self.warning_color  # Yellow for targeted
            name_text += " [TARGETED]"
        else:
            name_color = self.enemy_color
        
        name_surface = self.font.render(name_text, True, name_color)
        screen.blit(name_surface, (self.rect.x + 10, y))
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
        
        end_y = y + 20
        
        # Draw highlight background AFTER all content is drawn (so we know the actual height)
        if is_targeted:
            highlight_height = end_y - start_y + 10  # Full height of enemy info + padding
            highlight_rect = pygame.Rect(self.rect.x + 5, start_y - 5, self.rect.width - 10, highlight_height)
            # Draw background highlight with transparency effect
            highlight_surface = pygame.Surface((self.rect.width - 10, highlight_height))
            highlight_surface.set_alpha(80)  # Semi-transparent
            highlight_surface.fill((80, 40, 40))  # Dark red highlight
            screen.blit(highlight_surface, (self.rect.x + 5, start_y - 5))
            # Draw border
            pygame.draw.rect(screen, self.warning_color, highlight_rect, 2)  # Yellow border
        
        return end_y
    
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
    

def create_enemy_scan_panel(x, y, width, height, font):
    """Factory function to create an enemy scan panel."""
    return EnemyScanPanel(x, y, width, height, font)