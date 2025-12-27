"""
Enemy Scan Panel - Dedicated panel for displaying enemy scan results
LCARS-style panel that shows detailed information about scanned enemies
Matches the player ship status display format for consistency
"""

import pygame
import math

class EnemyScanPanel:
    """
    LCARS-style enemy scan panel showing (matching player ship display):
    - Warp Core Energy
    - Power Allocation (0-9 scale, read-only)
    - System Integrity (0-100 scale)
    - Shield Status
    - Weapon Status
    """

    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.small_font = pygame.font.Font(None, 14)
        self.medium_font = pygame.font.Font(None, 16)
        self.large_font = pygame.font.Font(None, 20)

        # LCARS Colors - Enemy themed (red/orange)
        self.bg_color = (40, 20, 20)        # Dark red background
        self.border_color = (255, 102, 102)  # LCARS red
        self.text_color = (255, 255, 255)    # White text
        self.enemy_color = (255, 80, 80)     # Enemy red
        self.warning_color = (255, 255, 0)   # Yellow warning
        self.critical_color = (255, 40, 40)  # Critical red
        self.good_color = (80, 255, 80)      # Green for good status
        self.bar_bg_color = (60, 40, 40)     # Dark bar background

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
            'energy': enemy_data.get('energy', 1000),
            'max_energy': enemy_data.get('max_energy', 1000),
            'weapons': enemy_data.get('weapons', []),
            'distance': enemy_data.get('distance', 0),
            'bearing': enemy_data.get('bearing', 0),
            'threat_level': enemy_data.get('threat_level', 'Unknown'),
            'system_integrity': enemy_data.get('system_integrity', {
                'hull': 100, 'shields': 100, 'phasers': 100,
                'engines': 100, 'warp_core': 100
            }),
            'power_allocation': enemy_data.get('power_allocation', {
                'phasers': 5, 'shields': 5, 'engines': 5
            }),
            'weapons_status': enemy_data.get('weapons_status', 'Online'),
            'engine_status': enemy_data.get('engine_status', 'Online'),
            'torpedo_count': enemy_data.get('torpedo_count', 6),
            'max_torpedoes': enemy_data.get('max_torpedoes', 6),
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
            if self.selected_enemy_id == enemy_id:
                if self.scanned_enemies:
                    self.selected_enemy_id = next(iter(self.scanned_enemies.keys()))
                else:
                    self.selected_enemy_id = None

    def select_enemy(self, enemy_id):
        """Select an enemy to display details."""
        if enemy_id in self.scanned_enemies:
            self.selected_enemy_id = enemy_id

    def draw(self, screen, targeted_enemy_id=None):
        """Draw the enemy scan panel showing all scanned enemies."""
        # Background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        # Title
        title_text = self.large_font.render("ENEMY TACTICAL SCAN", True, self.border_color)
        screen.blit(title_text, (self.rect.x + 10, self.rect.y + 5))

        current_y = self.rect.y + 28

        if not self.scanned_enemies:
            # No scan data
            no_data_text = self.font.render("No enemies scanned", True, self.text_color)
            screen.blit(no_data_text, (self.rect.x + 10, current_y))

            instruction_text = self.small_font.render("Right-click enemies to scan", True, (150, 150, 150))
            screen.blit(instruction_text, (self.rect.x + 10, current_y + 25))
        else:
            # Calculate available height per enemy
            num_enemies = len(self.scanned_enemies)
            available_height = self.rect.height - 35  # Account for title
            height_per_enemy = available_height // max(num_enemies, 1)

            # Draw all scanned enemies
            for i, (enemy_id, enemy_data) in enumerate(self.scanned_enemies.items()):
                is_targeted = (targeted_enemy_id == enemy_id)
                enemy_height = min(height_per_enemy - 5, 280)  # Cap height per enemy
                current_y = self.draw_enemy_status(screen, current_y, enemy_data,
                                                   is_targeted, i + 1, enemy_height)
                current_y += 5  # Small gap between enemies

    def draw_enemy_status(self, screen, y, enemy_data, is_targeted=False,
                          enemy_number=1, max_height=280):
        """Draw detailed status for an enemy (matching player ship format)."""
        start_y = y

        # Draw highlight background for targeted enemy
        if is_targeted:
            highlight_rect = pygame.Rect(self.rect.x + 3, y - 2,
                                        self.rect.width - 6, max_height)
            pygame.draw.rect(screen, (60, 30, 30), highlight_rect)
            pygame.draw.rect(screen, self.warning_color, highlight_rect, 2)

        # Enemy name/title with status
        name_text = f"{enemy_number}. {enemy_data['name']}"
        if is_targeted:
            name_color = self.warning_color
            name_text += " [TARGET]"
        else:
            name_color = self.enemy_color

        name_surface = self.medium_font.render(name_text, True, name_color)
        screen.blit(name_surface, (self.rect.x + 8, y))
        y += 16

        # Range and bearing on one line
        range_text = f"Range: {enemy_data['distance']:.1f}km  Bearing: {enemy_data['bearing']:.0f}°"
        range_surface = self.small_font.render(range_text, True, self.text_color)
        screen.blit(range_surface, (self.rect.x + 8, y))
        y += 14

        # Warp Core Energy
        y = self.draw_energy_bar(screen, y, "ENERGY",
                                 enemy_data['energy'], enemy_data['max_energy'])

        # Power Allocation (compact, read-only)
        y = self.draw_power_allocation(screen, y, enemy_data['power_allocation'])

        # System Integrity
        y = self.draw_system_integrity(screen, y, enemy_data)

        # Shield Status
        y = self.draw_shield_status(screen, y, enemy_data)

        # Weapon Status
        y = self.draw_weapon_status(screen, y, enemy_data)

        return max(y, start_y + max_height)

    def draw_energy_bar(self, screen, y, label, current, maximum):
        """Draw energy status bar."""
        label_surface = self.small_font.render(label, True, self.border_color)
        screen.blit(label_surface, (self.rect.x + 8, y))

        # Energy bar
        bar_width = self.rect.width - 70
        bar_height = 10
        bar_x = self.rect.x + 8
        bar_y = y + 12

        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, self.bar_bg_color, bar_rect)

        # Energy fill
        if maximum > 0:
            ratio = current / maximum
            fill_width = int(bar_width * ratio)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)

            if ratio > 0.6:
                color = self.good_color
            elif ratio > 0.3:
                color = self.warning_color
            else:
                color = self.critical_color

            pygame.draw.rect(screen, color, fill_rect)

        pygame.draw.rect(screen, self.border_color, bar_rect, 1)

        # Value text
        value_text = f"{int(current)}/{int(maximum)}"
        value_surface = self.small_font.render(value_text, True, self.text_color)
        screen.blit(value_surface, (bar_x + bar_width + 5, y + 10))

        return y + 26

    def draw_power_allocation(self, screen, y, power_allocation):
        """Draw power allocation meters (read-only, compact)."""
        label_surface = self.small_font.render("POWER ALLOCATION", True, self.border_color)
        screen.blit(label_surface, (self.rect.x + 8, y))
        y += 12

        systems = ['phasers', 'shields', 'engines']
        bar_width = 8
        bar_height = 10
        bar_spacing = 9

        for system in systems:
            power_level = power_allocation.get(system, 5)

            # System name (abbreviated)
            abbrev = system[:3].upper()
            system_text = self.small_font.render(f"{abbrev}:", True, self.text_color)
            screen.blit(system_text, (self.rect.x + 8, y))

            # Power level bars (1-9)
            bar_x = self.rect.x + 40

            for level in range(9):
                box_rect = pygame.Rect(bar_x + level * bar_spacing, y, bar_width, bar_height)

                if level < power_level:
                    if level < 3:
                        color = self.good_color
                    elif level < 6:
                        color = self.warning_color
                    else:
                        color = self.critical_color
                else:
                    color = self.bar_bg_color

                pygame.draw.rect(screen, color, box_rect)
                pygame.draw.rect(screen, self.border_color, box_rect, 1)

            # Power level number
            level_text = self.small_font.render(str(power_level), True, self.text_color)
            screen.blit(level_text, (bar_x + 9 * bar_spacing + 5, y))

            y += 13

        return y + 2

    def draw_system_integrity(self, screen, y, enemy_data):
        """Draw system integrity status (compact)."""
        label_surface = self.small_font.render("SYSTEM INTEGRITY", True, self.border_color)
        screen.blit(label_surface, (self.rect.x + 8, y))
        y += 12

        # Get system integrity data
        integrity = enemy_data.get('system_integrity', {})

        systems = [
            ('HULL', enemy_data['hull'], enemy_data['max_hull']),
            ('SHLD', integrity.get('shields', 100), 100),
            ('PHAS', integrity.get('phasers', 100), 100),
            ('ENG', integrity.get('engines', 100), 100),
            ('WARP', integrity.get('warp_core', 100), 100)
        ]

        bar_width = self.rect.width - 100
        bar_height = 8

        for abbrev, current, maximum in systems:
            # System abbreviation
            sys_text = self.small_font.render(f"{abbrev}:", True, self.text_color)
            screen.blit(sys_text, (self.rect.x + 8, y))

            # Integrity bar
            bar_x = self.rect.x + 45
            bar_rect = pygame.Rect(bar_x, y + 1, bar_width, bar_height)
            pygame.draw.rect(screen, self.bar_bg_color, bar_rect)

            # Fill
            if maximum > 0:
                ratio = current / maximum
                fill_width = int(bar_width * ratio)
                fill_rect = pygame.Rect(bar_x, y + 1, fill_width, bar_height)

                if ratio > 0.6:
                    color = self.good_color
                elif ratio > 0.3:
                    color = self.warning_color
                elif ratio > 0:
                    color = self.critical_color
                else:
                    color = (80, 80, 80)  # Gray for disabled

                pygame.draw.rect(screen, color, fill_rect)

            pygame.draw.rect(screen, self.border_color, bar_rect, 1)

            # Value and status
            if maximum > 0:
                ratio = current / maximum
                if ratio <= 0:
                    status = "OFF"
                    status_color = self.critical_color
                elif ratio < 0.3:
                    status = "CRIT"
                    status_color = self.critical_color
                elif ratio < 0.6:
                    status = "DMG"
                    status_color = self.warning_color
                else:
                    status = "OK"
                    status_color = self.good_color
            else:
                status = "---"
                status_color = (80, 80, 80)

            value_text = f"{int(current)}"
            value_surface = self.small_font.render(value_text, True, self.text_color)
            screen.blit(value_surface, (bar_x + bar_width + 3, y))

            status_surface = self.small_font.render(status, True, status_color)
            screen.blit(status_surface, (self.rect.x + self.rect.width - 30, y))

            y += 11

        return y + 2

    def draw_shield_status(self, screen, y, enemy_data):
        """Draw shield status."""
        label_surface = self.small_font.render("SHIELD STATUS", True, self.border_color)
        screen.blit(label_surface, (self.rect.x + 8, y))
        y += 12

        shields = enemy_data['shields']
        max_shields = enemy_data['max_shields']
        shield_power = enemy_data['power_allocation'].get('shields', 5)
        shield_integrity = enemy_data.get('system_integrity', {}).get('shields', 100)

        # Shield power and integrity
        power_text = f"Power: {shield_power}/9  Integrity: {shield_integrity:.0f}%"
        power_surface = self.small_font.render(power_text, True, self.text_color)
        screen.blit(power_surface, (self.rect.x + 8, y))
        y += 11

        # Absorption rate (based on power level)
        absorption = shield_power * 10  # 10 damage absorbed per power level
        absorb_text = f"Absorption: {absorption} per hit"
        absorb_surface = self.small_font.render(absorb_text, True, self.text_color)
        screen.blit(absorb_surface, (self.rect.x + 8, y))
        y += 11

        # Shield status
        if shield_power == 0:
            status_text = "SHIELDS DOWN"
            status_color = self.critical_color
        elif shield_integrity < 30:
            status_text = "SHIELDS FAILING"
            status_color = self.warning_color
        else:
            status_text = "SHIELDS UP"
            status_color = self.good_color

        status_surface = self.small_font.render(status_text, True, status_color)
        screen.blit(status_surface, (self.rect.x + 8, y))

        return y + 14

    def draw_weapon_status(self, screen, y, enemy_data):
        """Draw weapon systems status."""
        label_surface = self.small_font.render("WEAPON STATUS", True, self.border_color)
        screen.blit(label_surface, (self.rect.x + 8, y))
        y += 12

        weapons_status = enemy_data.get('weapons_status', 'Unknown')
        phaser_integrity = enemy_data.get('system_integrity', {}).get('phasers', 100)
        phaser_power = enemy_data['power_allocation'].get('phasers', 5)

        # Phaser status
        if phaser_integrity <= 0:
            phaser_text = "PHASERS: DISABLED"
            phaser_color = self.critical_color
        elif phaser_power == 0:
            phaser_text = "PHASERS: OFFLINE"
            phaser_color = self.warning_color
        elif weapons_status == 'Online':
            phaser_text = f"PHASERS: READY (PWR {phaser_power})"
            phaser_color = self.good_color
        else:
            phaser_text = f"PHASERS: {weapons_status}"
            phaser_color = self.warning_color

        phaser_surface = self.small_font.render(phaser_text, True, phaser_color)
        screen.blit(phaser_surface, (self.rect.x + 8, y))
        y += 11

        # Torpedo status
        torpedo_count = enemy_data.get('torpedo_count', 6)
        max_torpedoes = enemy_data.get('max_torpedoes', 6)

        if torpedo_count == 0:
            torpedo_text = "TORPEDOES: EMPTY"
            torpedo_color = self.critical_color
        elif torpedo_count <= max_torpedoes * 0.3:
            torpedo_text = f"TORPEDOES: {torpedo_count}/{max_torpedoes} (LOW)"
            torpedo_color = self.warning_color
        else:
            torpedo_text = f"TORPEDOES: {torpedo_count}/{max_torpedoes}"
            torpedo_color = self.good_color

        torpedo_surface = self.small_font.render(torpedo_text, True, torpedo_color)
        screen.blit(torpedo_surface, (self.rect.x + 8, y))
        y += 11

        # Engine status
        engine_status = enemy_data.get('engine_status', 'Unknown')
        engine_integrity = enemy_data.get('system_integrity', {}).get('engines', 100)
        engine_power = enemy_data['power_allocation'].get('engines', 5)

        if engine_integrity <= 0:
            engine_text = "ENGINES: DISABLED"
            engine_color = self.critical_color
        elif engine_power == 0:
            engine_text = "ENGINES: OFFLINE"
            engine_color = self.warning_color
        elif engine_integrity < 50:
            engine_text = f"ENGINES: DAMAGED ({engine_integrity:.0f}%)"
            engine_color = self.warning_color
        else:
            engine_text = f"ENGINES: ONLINE (PWR {engine_power})"
            engine_color = self.good_color

        engine_surface = self.small_font.render(engine_text, True, engine_color)
        screen.blit(engine_surface, (self.rect.x + 8, y))

        return y + 14


def create_enemy_scan_panel(x, y, width, height, font):
    """Factory function to create an enemy scan panel."""
    return EnemyScanPanel(x, y, width, height, font)
