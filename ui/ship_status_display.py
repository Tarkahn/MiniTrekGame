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
        
        # Title with critical status alert
        title_text = f"{ship.name} STATUS"
        title_color = self.border_color
        
        # Check for critical ship state
        if hasattr(ship, 'ship_state'):
            if ship.ship_state == "hull_breach":
                title_text = f"*** {ship.name} HULL BREACH ***"
                title_color = self.critical_color
            elif ship.ship_state == "warp_core_breach":
                title_text = f"*** {ship.name} EXPLODING ***"
                title_color = self.critical_color
            elif ship.ship_state == "destroyed":
                title_text = f"*** {ship.name} DESTROYED ***"
                title_color = (128, 128, 128)  # Gray for destroyed
        
        title_surface = self.large_font.render(title_text, True, title_color)
        screen.blit(title_surface, (self.rect.x + 10, self.rect.y + 5))
        
        # Show warp core breach countdown if applicable
        current_y = self.rect.y + 35
        if hasattr(ship, 'warp_core_breach_countdown') and ship.warp_core_breach_countdown > 0:
            countdown_text = f"WARP CORE BREACH IN {ship.warp_core_breach_countdown:.1f}s"
            countdown_surface = self.font.render(countdown_text, True, self.critical_color)
            screen.blit(countdown_surface, (self.rect.x + 10, current_y))
            current_y += 25
        
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
        
        # Get effective maximum energy (affected by warp core damage)
        effective_max_energy = ship.get_effective_max_energy() if hasattr(ship, 'get_effective_max_energy') else ship.max_warp_core_energy
        
        # Energy fill
        energy_ratio = ship.warp_core_energy / effective_max_energy if effective_max_energy > 0 else 0
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
        
        # Energy text - show damage indicator if warp core is damaged (display as integers)
        if effective_max_energy < ship.max_warp_core_energy:
            energy_text = f"{int(ship.warp_core_energy)}/{int(effective_max_energy)} (MAX: {int(ship.max_warp_core_energy)})"
        else:
            energy_text = f"{int(ship.warp_core_energy)}/{int(effective_max_energy)}"
        text_surface = self.small_font.render(energy_text, True, self.text_color)
        text_rect = text_surface.get_rect(center=bar_rect.center)
        screen.blit(text_surface, text_rect)
        
        return y + 50
    
    def draw_power_allocation(self, screen, ship, y):
        """Draw power allocation for all systems."""
        label = self.font.render("POWER ALLOCATION", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        y += 25
        
        systems = ['phasers', 'shields', 'engines']
        
        for i, system in enumerate(systems):
            power_level = ship.power_allocation.get(system, 0)
            
            # System name
            system_text = self.small_font.render(f"{system.upper()}:", True, self.text_color)
            screen.blit(system_text, (self.rect.x + 10, y))
            
            # ON/OFF button (left of meter)
            off_button_x = self.rect.x + 75
            off_button_rect = pygame.Rect(off_button_x, y, 15, 15)
            if power_level == 0:
                # System is off - red button
                pygame.draw.rect(screen, self.critical_color, off_button_rect)
                off_text = "0"
            else:
                # System is on - dark button
                pygame.draw.rect(screen, self.bar_bg_color, off_button_rect)
                off_text = "0"
            pygame.draw.rect(screen, self.border_color, off_button_rect, 1)
            off_label = self.small_font.render(off_text, True, self.text_color)
            off_label_rect = off_label.get_rect(center=off_button_rect.center)
            screen.blit(off_label, off_label_rect)
            
            # Power level bars (1-9)
            bar_x = self.rect.x + 100
            bar_width = 10
            bar_height = 15
            bar_spacing = 12
            
            for level in range(9):  # 9 power level boxes (1-9)
                bar_rect = pygame.Rect(bar_x + level * bar_spacing, y, bar_width, bar_height)
                
                # Show filled bars based on current power level
                # level 0 = box 1, level 1 = box 2, etc.
                if level < power_level and power_level > 0:
                    # Filled bar (only if system has power)
                    if level < 3:
                        color = self.good_color
                    elif level < 7:
                        color = self.warning_color
                    else:
                        color = self.critical_color
                else:
                    # Empty bar or system is off
                    if power_level == 0:
                        color = (40, 40, 40)  # Very dark when system is off
                    else:
                        color = self.bar_bg_color
                
                pygame.draw.rect(screen, color, bar_rect)
                pygame.draw.rect(screen, self.border_color, bar_rect, 1)
            
            # MAX button (right of meter)
            max_button_x = bar_x + 115  # After the 9 meter boxes
            max_button_rect = pygame.Rect(max_button_x, y, 20, 15)
            if power_level == 9:
                # System is at max - bright button
                pygame.draw.rect(screen, self.warning_color, max_button_rect)
            else:
                # System not at max - dark button
                pygame.draw.rect(screen, self.bar_bg_color, max_button_rect)
            pygame.draw.rect(screen, self.border_color, max_button_rect, 1)
            # Use smaller font for MAX button
            tiny_font = pygame.font.Font(None, 14)
            max_label = tiny_font.render("MAX", True, self.text_color)
            max_label_rect = max_label.get_rect(center=max_button_rect.center)
            screen.blit(max_label, max_label_rect)
            
            # Power level number
            level_text = self.small_font.render(str(power_level), True, self.text_color)
            screen.blit(level_text, (bar_x + 145, y))
            
            y += 20
        
        return y
    
    def handle_click(self, pos, ship):
        """Handle mouse clicks on power allocation bars."""
        if not self.rect.collidepoint(pos):
            return False
        
        # Check if click is in power allocation area
        systems = ['phasers', 'shields', 'engines']
        
        # Use exact coordinates for power allocation bars
        system_coordinates = [160, 180, 200, 220]  # Phasers, Shields, Engines, Sensors
        
        for i, system in enumerate(systems):
            system_y = system_coordinates[i]
            
            # Check if click is in this system's row
            if system_y <= pos[1] <= system_y + 15:  # 15 pixels height per row
                
                # Check for OFF button click (left of meter)
                off_button_x = self.rect.x + 75
                if off_button_x <= pos[0] <= off_button_x + 15:
                    # Turn system off (set power to 0)
                    if ship.allocate_power(system, 0):
                        return True
                
                # Check for MAX button click (right of meter)
                max_button_x = self.rect.x + 100 + 115  # bar_x + 115
                if max_button_x <= pos[0] <= max_button_x + 20:
                    # Set system to maximum power (9)
                    if ship.allocate_power(system, 9):
                        return True
                
                # Check for power meter clicks
                bar_x = self.rect.x + 100
                bar_spacing = 12
                
                if bar_x <= pos[0] <= bar_x + (9 * bar_spacing):  # Within meter area
                    # Calculate which box was clicked (0-8 for 9 boxes)
                    clicked_box = (pos[0] - bar_x) // bar_spacing
                    
                    # Set power level to the clicked box number + 1
                    # Box 0 = power 1, Box 1 = power 2, ..., Box 8 = power 9
                    if 0 <= clicked_box <= 8:
                        new_power_level = clicked_box + 1
                        
                        # Attempt to allocate power
                        if ship.allocate_power(system, new_power_level):
                            return True
                        
        return False
    
    def draw_system_integrity(self, screen, ship, y):
        """Draw system integrity status."""
        label = self.font.render("SYSTEM INTEGRITY", True, self.border_color)
        screen.blit(label, (self.rect.x + 10, y))
        y += 25
        
        systems = ['hull', 'shields', 'phasers', 'engines', 'warp_core']
        
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
                integrity_value = int(ship.hull_strength)
                max_value = int(ship.max_hull_strength)
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
            y += 18
        
        # Engine efficiency display
        if hasattr(ship, 'get_engine_efficiency'):
            engine_power = ship.power_allocation.get('engines', 5)
            efficiency = ship.get_engine_efficiency()
            engine_integrity = ship.system_integrity.get('engines', 100)
            
            # Color based on efficiency
            if efficiency >= 1.0:
                efficiency_color = self.good_color
            elif efficiency >= 0.7:
                efficiency_color = self.warning_color
            else:
                efficiency_color = self.critical_color
            
            engine_text = f"ENGINE POWER: {engine_power}/9 - Efficiency: {efficiency:.1f}x"
            engine_surface = self.small_font.render(engine_text, True, efficiency_color)
            screen.blit(engine_surface, (self.rect.x + 10, y))
            y += 18
            
            # Engine status
            if engine_integrity < 100:
                damage_text = f"Engine Damage: {100-engine_integrity:.0f}% (Reduces Speed)"
                damage_surface = self.small_font.render(damage_text, True, self.critical_color)
                screen.blit(damage_surface, (self.rect.x + 10, y))
                y += 18
        
        # Torpedo status
        if hasattr(ship, 'torpedo_count'):
            torpedo_count = ship.torpedo_count
            max_torpedoes = ship.max_torpedo_capacity
            
            # Torpedo count with color coding
            if torpedo_count > max_torpedoes * 0.6:
                torpedo_color = self.good_color
            elif torpedo_count > max_torpedoes * 0.3:
                torpedo_color = self.warning_color
            elif torpedo_count > 0:
                torpedo_color = self.critical_color
            else:
                torpedo_color = self.critical_color
            
            torpedo_text = f"TORPEDOES: {torpedo_count}/{max_torpedoes}"
            torpedo_surface = self.small_font.render(torpedo_text, True, torpedo_color)
            screen.blit(torpedo_surface, (self.rect.x + 10, y))
            y += 18
            
            # Torpedo status indicator
            if torpedo_count == 0:
                status_text = "NO TORPEDOES"
                status_color = self.critical_color
            elif torpedo_count <= max_torpedoes * 0.3:
                status_text = "LOW AMMUNITION"
                status_color = self.warning_color
            else:
                status_text = "READY"
                status_color = self.good_color
            
            status_surface = self.small_font.render(status_text, True, status_color)
            screen.blit(status_surface, (self.rect.x + 10, y))
        
        return y + 25

def create_ship_status_display(x, y, width, height, font):
    """Factory function to create a ship status display."""
    return ShipStatusDisplay(x, y, width, height, font)