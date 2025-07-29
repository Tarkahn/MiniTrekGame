import pygame
import math
import random


class EnemyPopupManager:
    """Manages enemy ship popup windows and scanning functionality."""
    
    def __init__(self, screen, fonts):
        self.screen = screen
        self.font = fonts['regular']
        self.small_font = fonts['small']
        self.title_font = fonts['title']
        self.enemy_popups = {}
        self.targeted_enemies = {}
        self.next_enemy_id = 1
    
    def create_popup(self, enemy_id, enemy_obj, popup_dock_x, popup_height=350):
        """Create a popup window for enemy ship stats."""
        # Calculate popup window dimensions and position
        popup_width = 280
        # Position popups in the dedicated dock area
        popup_x = popup_dock_x + 10  # 10px padding from dock edge
        popup_y = 40 + 50 + (len(self.enemy_popups) * (popup_height + 10))  # Stack vertically
        
        # Initialize enemy stats if not present
        if not hasattr(enemy_obj, 'health'):
            enemy_obj.health = 100
        if not hasattr(enemy_obj, 'max_health'):
            enemy_obj.max_health = 100
        if not hasattr(enemy_obj, 'energy'):
            enemy_obj.energy = 1000
        if not hasattr(enemy_obj, 'max_energy'):
            enemy_obj.max_energy = 1000
        if not hasattr(enemy_obj, 'shields'):
            enemy_obj.shields = 100  # Start with full shields
        if not hasattr(enemy_obj, 'max_shields'):
            enemy_obj.max_shields = 100
        if not hasattr(enemy_obj, 'weapons_status'):
            enemy_obj.weapons_status = 'Online'
        if not hasattr(enemy_obj, 'engine_status'):
            enemy_obj.engine_status = 'Online'
        if not hasattr(enemy_obj, 'distance'):
            enemy_obj.distance = 0.0
        if not hasattr(enemy_obj, 'bearing'):
            enemy_obj.bearing = 0.0
        
        # Initialize power allocation system (0-9 scale) at full power
        if not hasattr(enemy_obj, 'power_allocation'):
            enemy_obj.power_allocation = {
                'phasers': 9,      # Full power
                'shields': 9,      
                'impulse': 9,
                'sensors': 9,
                'life_support': 9
            }
        
        # Initialize system integrity (0-100 scale) at full integrity
        if not hasattr(enemy_obj, 'system_integrity'):
            enemy_obj.system_integrity = {
                'hull': 100,
                'shields': 100,
                'phasers': 100,
                'impulse': 100,
                'sensors': 100,
                'life_support': 100,
                'warp_core': 100
            }
        
        popup_info = {
            'rect': pygame.Rect(popup_x, popup_y, popup_width, popup_height),
            'enemy_obj': enemy_obj,
            'enemy_id': enemy_id,
            'font': self.font,
            'small_font': self.small_font,
            'title_font': self.title_font,
            'visible': False
        }
        
        return popup_info
    
    def draw_popup(self, popup_info):
        """Draw the enemy ship stats popup window."""
        if not popup_info['visible']:
            return
        
        enemy = popup_info['enemy_obj']
        rect = popup_info['rect']
        font = popup_info['font']
        small_font = popup_info['small_font']
        title_font = popup_info['title_font']
        
        # Create a separate surface for the popup
        popup_surface = pygame.Surface((rect.width, rect.height))
        popup_surface.fill((40, 40, 60))
        
        # Draw border
        pygame.draw.rect(popup_surface, (100, 100, 150), popup_surface.get_rect(), 3)
        
        y_offset = 10
        
        # Ship name and class
        name_text = title_font.render(f"Enemy Ship #{popup_info['enemy_id']}", True, (255, 255, 255))
        popup_surface.blit(name_text, (10, y_offset))
        y_offset += 30
        
        class_text = font.render(f"Class: {getattr(enemy, 'ship_class', 'Unknown')}", True, (200, 200, 200))
        popup_surface.blit(class_text, (10, y_offset))
        y_offset += 25
        
        # Position info
        bearing_text = small_font.render(f"Bearing: {enemy.bearing:.0f}°", True, (150, 150, 150))
        popup_surface.blit(bearing_text, (10, y_offset))
        distance_text = small_font.render(f"Distance: {enemy.distance:.1f} sectors", True, (150, 150, 150))
        popup_surface.blit(distance_text, (140, y_offset))
        y_offset += 25
        
        # Health bar
        health_percent = enemy.health / enemy.max_health
        health_color = (0, 255, 0) if health_percent > 0.5 else (255, 255, 0) if health_percent > 0.25 else (255, 0, 0)
        health_text = small_font.render("Hull:", True, (200, 200, 200))
        popup_surface.blit(health_text, (10, y_offset))
        
        bar_x = 60
        bar_width = 200
        bar_height = 20
        pygame.draw.rect(popup_surface, (60, 60, 60), (bar_x, y_offset, bar_width, bar_height))
        pygame.draw.rect(popup_surface, health_color, (bar_x, y_offset, int(bar_width * health_percent), bar_height))
        pygame.draw.rect(popup_surface, (100, 100, 100), (bar_x, y_offset, bar_width, bar_height), 2)
        
        health_value_text = small_font.render(f"{enemy.health}/{enemy.max_health}", True, (255, 255, 255))
        text_rect = health_value_text.get_rect(center=(bar_x + bar_width // 2, y_offset + bar_height // 2))
        popup_surface.blit(health_value_text, text_rect)
        y_offset += 30
        
        # Shield bar
        shield_percent = enemy.shields / enemy.max_shields
        shield_color = (0, 200, 255) if shield_percent > 0.5 else (0, 150, 200) if shield_percent > 0.25 else (0, 100, 150)
        shield_text = small_font.render("Shields:", True, (200, 200, 200))
        popup_surface.blit(shield_text, (10, y_offset))
        
        pygame.draw.rect(popup_surface, (60, 60, 60), (bar_x, y_offset, bar_width, bar_height))
        pygame.draw.rect(popup_surface, shield_color, (bar_x, y_offset, int(bar_width * shield_percent), bar_height))
        pygame.draw.rect(popup_surface, (100, 100, 100), (bar_x, y_offset, bar_width, bar_height), 2)
        
        shield_value_text = small_font.render(f"{enemy.shields}/{enemy.max_shields}", True, (255, 255, 255))
        text_rect = shield_value_text.get_rect(center=(bar_x + bar_width // 2, y_offset + bar_height // 2))
        popup_surface.blit(shield_value_text, text_rect)
        y_offset += 30
        
        # Energy level
        energy_percent = enemy.energy / enemy.max_energy
        energy_color = (255, 255, 0) if energy_percent > 0.5 else (200, 200, 0) if energy_percent > 0.25 else (150, 150, 0)
        energy_text = small_font.render("Energy:", True, (200, 200, 200))
        popup_surface.blit(energy_text, (10, y_offset))
        
        pygame.draw.rect(popup_surface, (60, 60, 60), (bar_x, y_offset, bar_width, bar_height))
        pygame.draw.rect(popup_surface, energy_color, (bar_x, y_offset, int(bar_width * energy_percent), bar_height))
        pygame.draw.rect(popup_surface, (100, 100, 100), (bar_x, y_offset, bar_width, bar_height), 2)
        
        energy_value_text = small_font.render(f"{enemy.energy}/{enemy.max_energy}", True, (255, 255, 255))
        text_rect = energy_value_text.get_rect(center=(bar_x + bar_width // 2, y_offset + bar_height // 2))
        popup_surface.blit(energy_value_text, text_rect)
        y_offset += 35
        
        # Systems status
        weapons_color = (0, 255, 0) if enemy.weapons_status == 'Online' else (255, 255, 0) if enemy.weapons_status == 'Damaged' else (255, 0, 0)
        weapons_text = small_font.render(f"Weapons: {enemy.weapons_status}", True, weapons_color)
        popup_surface.blit(weapons_text, (10, y_offset))
        y_offset += 20
        
        engine_color = (0, 255, 0) if enemy.engine_status == 'Online' else (255, 255, 0) if enemy.engine_status == 'Damaged' else (255, 0, 0)
        engine_text = small_font.render(f"Engines: {enemy.engine_status}", True, engine_color)
        popup_surface.blit(engine_text, (10, y_offset))
        y_offset += 25
        
        # Threat assessment
        threat_level = "High" if health_percent > 0.7 and enemy.weapons_status == 'Online' else "Medium" if health_percent > 0.3 else "Low"
        threat_color = (255, 0, 0) if threat_level == "High" else (255, 255, 0) if threat_level == "Medium" else (0, 255, 0)
        threat_text = font.render("Threat Level:", True, (200, 200, 200))
        popup_surface.blit(threat_text, (10, y_offset))
        threat_level_text = font.render(threat_level, True, threat_color)
        popup_surface.blit(threat_level_text, (20, y_offset))
        
        # Blit popup to main screen in the designated dock area
        self.screen.blit(popup_surface, rect.topleft)
    
    def update_popups(self, systems, current_system, event_log_callback):
        """Update and clean up enemy popups for destroyed ships."""
        destroyed_enemies = []
        for enemy_id, popup_info in self.enemy_popups.items():
            enemy = popup_info['enemy_obj']
            # Check if enemy is destroyed
            if not hasattr(enemy, 'health') or enemy.health <= 0:
                destroyed_enemies.append(enemy_id)
            # Check if enemy is still in current system
            elif enemy not in systems.get(current_system, []):
                destroyed_enemies.append(enemy_id)
        
        # Remove destroyed enemies from tracking
        for enemy_id in destroyed_enemies:
            if enemy_id in self.enemy_popups:
                del self.enemy_popups[enemy_id]
            if enemy_id in self.targeted_enemies:
                del self.targeted_enemies[enemy_id]
                event_log_callback(f"Target {enemy_id} lost - popup closed")
    
    def get_enemy_id(self, enemy_obj):
        """Get or assign a unique ID to an enemy object."""
        # Check if this enemy already has an ID
        for enemy_id, tracked_enemy in self.targeted_enemies.items():
            if tracked_enemy is enemy_obj:
                return enemy_id
        
        # Assign new ID
        enemy_id = self.next_enemy_id
        self.next_enemy_id += 1
        return enemy_id
    
    def perform_scan(self, enemy_obj, enemy_id, player_obj, event_log_callback):
        """Perform a detailed scan of an enemy and add results to scan panel."""
        # Calculate distance from player
        if player_obj and hasattr(player_obj, 'system_q') and hasattr(player_obj, 'system_r'):
            dx = enemy_obj.system_q - player_obj.system_q
            dy = enemy_obj.system_r - player_obj.system_r
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Calculate bearing (0-360 degrees)
            bearing = math.degrees(math.atan2(dy, dx))
            if bearing < 0:
                bearing += 360
        else:
            distance = 0
            bearing = 0
        
        # Generate realistic enemy data (simulate scan results)
        enemy_obj.distance = distance
        enemy_obj.bearing = bearing
        enemy_obj.ship_class = random.choice(["Bird of Prey", "D7 Cruiser", "Warbird", "Marauder", "Scout"])
        
        # Random damage states
        if random.random() < 0.3:
            enemy_obj.weapons_status = random.choice(["Damaged", "Offline"])
        if random.random() < 0.2:
            enemy_obj.engine_status = random.choice(["Damaged", "Offline"])
        
        # Add scan log entries
        event_log_callback(f"[SCAN] Enemy ship #{enemy_id} detected")
        event_log_callback(f"[SCAN] Class: {enemy_obj.ship_class}")
        event_log_callback(f"[SCAN] Distance: {distance:.1f} sectors")
        event_log_callback(f"[SCAN] Bearing: {bearing:.0f}°")
        event_log_callback(f"[SCAN] Hull integrity: {enemy_obj.health}%")
        event_log_callback(f"[SCAN] Shield strength: {enemy_obj.shields}%")
        if enemy_obj.weapons_status != 'Online':
            event_log_callback(f"[SCAN] WARNING: Weapons {enemy_obj.weapons_status.lower()}")
        if enemy_obj.engine_status != 'Online':
            event_log_callback(f"[SCAN] WARNING: Engines {enemy_obj.engine_status.lower()}")