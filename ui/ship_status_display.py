"""
Ship Status Display - Shows power allocation, system integrity, and energy status
PRD-compliant display for tactical decision making
"""

import pygame
from data.constants import *

class ShipStatusDisplay:
    """
    LCARS-style ship status display showing:
    - Warp Core Energy
    - Power Allocation (0-9 scale)
    - System Integrity (0-100 scale)
    - Shield Status
    - Weapon Status
    """
    
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.small_font = pygame.font.Font(None, 18)
        self.large_font = pygame.font.Font(None, 24)
        
        # LCARS Colors
        self.bg_color = (20, 20, 40)        # Dark blue background
        self.border_color = (255, 204, 102)  # LCARS orange
        self.text_color = (255, 255, 255)    # White text
        self.good_color = (0, 255, 0)        # Green for good status
        self.warning_color = (255, 255, 0)   # Yellow for warning
        self.critical_color = (255, 0, 0)    # Red for critical
        self.bar_bg_color = (60, 60, 80)     # Dark bar background
        
    def draw(self, screen, ship):
        """Draw the complete ship status display."""
        # Background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Title
        title_text = self.large_font.render(f"{ship.name} STATUS", True, self.border_color)
        screen.blit(title_text, (self.rect.x + 10, self.rect.y + 5))
        
        current_y = self.rect.y + 35
        
        # Energy Status
        current_y = self.draw_energy_status(screen, ship, current_y)
        current_y += 10
        
        # Power Allocation
        current_y = self.draw_power_allocation(screen, ship, current_y)
        current_y += 10
        
        # System Integrity
        current_y = self.draw_system_integrity(screen, ship, current_y)
        current_y += 10
        
        # Shield Status
        current_y = self.draw_shield_status(screen, ship, current_y)
        current_y += 10
        
        # Weapon Status
        self.draw_weapon_status(screen, ship, current_y)
    
    def draw_energy_status(self, screen, ship, y):
        """Draw warp core energy status."""
        label = self.font.render("WARP CORE ENERGY", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        
        # Energy bar
        bar_rect = pygame.Rect(self.rect.x + 10, y + 20, self.rect.width - 20, 20)
        pygame.draw.rect(screen, self.bar_bg_color, bar_rect)
        
        # Energy fill
        energy_ratio = ship.warp_core_energy / ship.max_warp_core_energy
        fill_width = int((self.rect.width - 20) * energy_ratio)
        fill_rect = pygame.Rect(self.rect.x + 10, y + 20, fill_width, 20)
        
        # Color based on energy level
        if energy_ratio > 0.6:
            color = self.good_color
        elif energy_ratio > 0.3:
            color = self.warning_color
        else:
            color = self.critical_color
            
        pygame.draw.rect(screen, color, fill_rect)
        pygame.draw.rect(screen, self.border_color, bar_rect, 1)
        
        # Energy text
        energy_text = f"{ship.warp_core_energy}/{ship.max_warp_core_energy}"
        text_surface = self.small_font.render(energy_text, True, self.text_color)
        text_rect = text_surface.get_rect(center=bar_rect.center)
        screen.blit(text_surface, text_rect)
        
        return y + 50
    
    def draw_power_allocation(self, screen, ship, y):
        """Draw power allocation for all systems."""
        label = self.font.render("POWER ALLOCATION", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        y += 25
        
        systems = ['phasers', 'shields', 'engines', 'sensors', 'life_support']
        
        for i, system in enumerate(systems):
            power_level = ship.power_allocation.get(system, 0)
            
            # System name
            system_text = self.small_font.render(f"{system.upper()}:", True, self.text_color)
            screen.blit(system_text, (self.rect.x + 10, y))
            
            # Power level bars (0-9)
            bar_x = self.rect.x + 100
            bar_width = 10
            bar_height = 15
            bar_spacing = 12
            
            for level in range(10):  # 0-9 power levels
                bar_rect = pygame.Rect(bar_x + level * bar_spacing, y, bar_width, bar_height)
                
                if level < power_level:
                    # Filled bar
                    if level < 3:
                        color = self.good_color
                    elif level < 7:
                        color = self.warning_color
                    else:
                        color = self.critical_color
                else:
                    # Empty bar
                    color = self.bar_bg_color
                
                pygame.draw.rect(screen, color, bar_rect)
                pygame.draw.rect(screen, self.border_color, bar_rect, 1)
            
            # Power level number
            level_text = self.small_font.render(str(power_level), True, self.text_color)
            screen.blit(level_text, (bar_x + 125, y))
            
            y += 20
        
        return y
    
    def handle_click(self, pos, ship):
        """Handle mouse clicks on power allocation bars."""
        if not self.rect.collidepoint(pos):
            return False
        
        # Check if click is in power allocation area
        systems = ['phasers', 'shields', 'engines', 'sensors', 'life_support']
        
        # Calculate power allocation area bounds
        power_start_y = self.rect.y + 60  # Approximate start of power allocation section
        
        for i, system in enumerate(systems):
            system_y = power_start_y + (i * 20)  # 20 pixels per system row
            
            # Check if click is in this system's row
            if system_y <= pos[1] <= system_y + 15:  # 15 pixels height per row
                # Calculate which power level was clicked
                bar_x = self.rect.x + 100
                bar_spacing = 12
                
                if pos[0] >= bar_x:
                    clicked_level = (pos[0] - bar_x) // bar_spacing
                    
                    # Ensure clicked level is valid (0-9)
                    if 0 <= clicked_level <= 9:
                        # Set power to clicked level + 1 (since we want 1-based visual)
                        new_power_level = clicked_level + 1
                        if new_power_level > 9:
                            new_power_level = 9
                        
                        # Attempt to allocate power
                        if ship.allocate_power(system, new_power_level):
                            return True
                        
        return False
    
    def draw_system_integrity(self, screen, ship, y):
        """Draw system integrity status."""
        label = self.font.render("SYSTEM INTEGRITY", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        y += 25
        
        systems = ['hull', 'shields', 'phasers', 'engines', 'sensors', 'life_support', 'warp_core']
        
        for system in systems:
            integrity = ship.system_integrity.get(system, 100)
            
            # System name
            system_text = self.small_font.render(f"{system.upper()}:", True, self.text_color)
            screen.blit(system_text, (self.rect.x + 10, y))
            
            # Integrity bar
            bar_rect = pygame.Rect(self.rect.x + 100, y, 100, 15)
            pygame.draw.rect(screen, self.bar_bg_color, bar_rect)
            
            # Integrity fill
            if system == 'hull':
                # Hull uses actual hull strength
                integrity_ratio = ship.hull_strength / ship.max_hull_strength
                integrity_value = ship.hull_strength
                max_value = ship.max_hull_strength
            else:
                # Other systems use 0-100 scale
                integrity_ratio = integrity / 100.0
                integrity_value = int(integrity)
                max_value = 100
            
            fill_width = int(100 * integrity_ratio)
            fill_rect = pygame.Rect(self.rect.x + 100, y, fill_width, 15)
            
            # Color based on integrity
            if integrity_ratio > 0.6:
                color = self.good_color
            elif integrity_ratio > 0.3:
                color = self.warning_color
            elif integrity_ratio > 0:
                color = self.critical_color
            else:
                color = (128, 128, 128)  # Gray for disabled
            
            pygame.draw.rect(screen, color, fill_rect)
            pygame.draw.rect(screen, self.border_color, bar_rect, 1)
            
            # Integrity text
            integrity_text = f"{integrity_value}/{max_value}"
            text_surface = self.small_font.render(integrity_text, True, self.text_color)
            screen.blit(text_surface, (self.rect.x + 210, y))
            
            # Status indicator
            if integrity_ratio <= 0:
                status_text = "DISABLED"
                status_color = self.critical_color
            elif integrity_ratio < 0.3:
                status_text = "CRITICAL"
                status_color = self.critical_color
            elif integrity_ratio < 0.6:
                status_text = "DAMAGED"
                status_color = self.warning_color
            else:
                status_text = "NOMINAL"
                status_color = self.good_color
            
            status_surface = self.small_font.render(status_text, True, status_color)
            screen.blit(status_surface, (self.rect.x + 270, y))
            
            y += 18
        
        return y
    
    def draw_shield_status(self, screen, ship, y):
        """Draw detailed shield status."""
        label = self.font.render("SHIELD STATUS", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        y += 25
        
        shield = ship.shield_system
        
        # Shield Power Level
        power_text = f"Power Level: {shield.current_power_level}/{shield.max_power_level}"
        power_surface = self.small_font.render(power_text, True, self.text_color)
        screen.blit(power_surface, (self.rect.x + 10, y))
        y += 18
        
        # Shield Integrity
        integrity_text = f"Integrity: {shield.current_integrity:.1f}/100"
        integrity_surface = self.small_font.render(integrity_text, True, self.text_color)
        screen.blit(integrity_surface, (self.rect.x + 10, y))
        y += 18
        
        # Shield Effectiveness
        absorption = shield.current_power_level * shield.absorption_per_level
        effect_text = f"Absorption: {absorption} damage per attack"
        effect_surface = self.small_font.render(effect_text, True, self.text_color)
        screen.blit(effect_surface, (self.rect.x + 10, y))
        y += 18
        
        # Shield Status
        if shield.current_power_level == 0:
            status_text = "SHIELDS DOWN"
            status_color = self.critical_color
        elif shield.current_integrity < 30:
            status_text = "SHIELDS FAILING"
            status_color = self.warning_color
        else:
            status_text = "SHIELDS UP"
            status_color = self.good_color
        
        status_surface = self.small_font.render(status_text, True, status_color)
        screen.blit(status_surface, (self.rect.x + 10, y))
        
        return y + 25
    
    def draw_weapon_status(self, screen, ship, y):
        """Draw weapon systems status."""
        label = self.font.render("WEAPON STATUS", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        y += 25
        
        # Phaser status
        if hasattr(ship, 'phaser_system'):
            phaser = ship.phaser_system
            
            # Phaser ready status
            if phaser.is_on_cooldown():
                cooldown_time = (phaser._last_fired_time + phaser.cooldown_seconds) - pygame.time.get_ticks() / 1000.0
                status_text = f"PHASERS: RECHARGING ({cooldown_time:.1f}s)"
                status_color = self.warning_color
            else:
                status_text = "PHASERS: READY"
                status_color = self.good_color
            
            status_surface = self.small_font.render(status_text, True, status_color)
            screen.blit(status_surface, (self.rect.x + 10, y))
            y += 18
            
            # Phaser power and range
            power_level = ship.power_allocation.get('phasers', 5)
            power_modifier = power_level / 5.0
            range_text = f"Range: {phaser.range} hexes, Power: {power_modifier:.1f}x"
            range_surface = self.small_font.render(range_text, True, self.text_color)
            screen.blit(range_surface, (self.rect.x + 10, y))
        
        return y + 25

def create_ship_status_display(x, y, width, height, font):
    """Factory function to create a ship status display."""
    return ShipStatusDisplay(x, y, width, height, font)