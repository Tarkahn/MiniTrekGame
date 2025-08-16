"""
Combat Manager - Handles all combat-related game logic
Separates combat mechanics from UI code for better architecture
Includes enemy AI and movement management
"""

from data import constants
from ship.enemy_ship import EnemyShip


class CombatManager:
    """
    Manages all combat interactions between ships, weapons, and targets.
    Provides a clean interface for combat actions while maintaining separation
    of concerns between game logic and UI.
    """
    
    def __init__(self):
        # Enemy AI management
        self.enemy_ships = {}  # Dictionary to store EnemyShip instances keyed by enemy object id
    
    def fire_phasers(self, attacker_ship, target_enemy, distance):
        """
        Execute a phaser attack from attacker to target.
        
        Args:
            attacker_ship: Ship object with phaser system
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes between attacker and target
            
        Returns:
            dict: Combat result with damage dealt, range description, etc.
        """
        # Use the ship's phaser system for proper power allocation and calculations
        damage = attacker_ship.phaser_system.fire(int(distance))
        
        # Determine range description for UI display
        if distance <= constants.PHASER_CLOSE_RANGE:
            range_description = "CLOSE RANGE"
        elif distance <= constants.PHASER_MEDIUM_RANGE:
            range_description = "MEDIUM RANGE"
        else:
            range_description = "LONG RANGE"
        
        # Initialize enemy attributes if they don't exist (always, regardless of damage)
        if not hasattr(target_enemy, 'shields'):
            target_enemy.shields = constants.ENEMY_SHIELD_CAPACITY
        if not hasattr(target_enemy, 'max_shields'):
            target_enemy.max_shields = constants.ENEMY_SHIELD_CAPACITY
        if not hasattr(target_enemy, 'health'):
            target_enemy.health = constants.ENEMY_HULL_STRENGTH
        if not hasattr(target_enemy, 'max_health'):
            target_enemy.max_health = constants.ENEMY_HULL_STRENGTH
        
        # Apply damage to target if any was dealt
        damage_applied = 0
        shield_damage = 0
        hull_damage = 0
        target_destroyed = False
        
        if damage > 0:
            
            remaining_damage = damage
            
            # Shields absorb damage first
            if target_enemy.shields > 0:
                shield_damage = min(remaining_damage, target_enemy.shields)
                target_enemy.shields -= shield_damage
                remaining_damage -= shield_damage
            
            # Remaining damage goes to hull
            if remaining_damage > 0 and target_enemy.shields <= 0:
                hull_damage = min(remaining_damage, target_enemy.health)
                target_enemy.health -= hull_damage
                remaining_damage -= hull_damage
            
            damage_applied = damage - remaining_damage
            target_destroyed = target_enemy.health <= 0
        
        # Return comprehensive combat result
        return {
            'damage_calculated': damage,
            'damage_applied': damage_applied,
            'shield_damage': shield_damage,
            'hull_damage': hull_damage,
            'distance': distance,
            'range_description': range_description,
            'target_destroyed': target_destroyed,
            'target_shields': getattr(target_enemy, 'shields', 0),
            'target_max_shields': getattr(target_enemy, 'max_shields', 0),
            'target_health': getattr(target_enemy, 'health', 0),
            'target_max_health': getattr(target_enemy, 'max_health', 0),
            'success': True  # Always show effects if combat manager was called
        }
    
    def fire_torpedoes(self, attacker_ship, target_enemy, distance):
        """
        Execute a torpedo attack from attacker to target.
        
        Args:
            attacker_ship: Ship object with torpedo system
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes between attacker and target
            
        Returns:
            dict: Combat result similar to fire_phasers
        """
        # Use the ship's torpedo system
        damage = attacker_ship.torpedo_system.fire(int(distance))
        
        # Initialize enemy attributes if they don't exist (always, regardless of damage)
        if not hasattr(target_enemy, 'shields'):
            target_enemy.shields = constants.ENEMY_SHIELD_CAPACITY
        if not hasattr(target_enemy, 'max_shields'):
            target_enemy.max_shields = constants.ENEMY_SHIELD_CAPACITY
        if not hasattr(target_enemy, 'health'):
            target_enemy.health = constants.ENEMY_HULL_STRENGTH
        if not hasattr(target_enemy, 'max_health'):
            target_enemy.max_health = constants.ENEMY_HULL_STRENGTH
        
        # Apply damage to target if any was dealt
        damage_applied = 0
        shield_damage = 0
        hull_damage = 0
        target_destroyed = False
        
        if damage > 0:
            
            remaining_damage = damage
            
            # Shields absorb damage first
            if target_enemy.shields > 0:
                shield_damage = min(remaining_damage, target_enemy.shields)
                target_enemy.shields -= shield_damage
                remaining_damage -= shield_damage
            
            # Remaining damage goes to hull
            if remaining_damage > 0 and target_enemy.shields <= 0:
                hull_damage = min(remaining_damage, target_enemy.health)
                target_enemy.health -= hull_damage
                remaining_damage -= hull_damage
            
            damage_applied = damage - remaining_damage
            target_destroyed = target_enemy.health <= 0
        
        # Return comprehensive combat result
        return {
            'damage_calculated': damage,
            'damage_applied': damage_applied,
            'shield_damage': shield_damage,
            'hull_damage': hull_damage,
            'distance': distance,
            'target_destroyed': target_destroyed,
            'target_shields': getattr(target_enemy, 'shields', 0),
            'target_max_shields': getattr(target_enemy, 'max_shields', 0),
            'target_health': getattr(target_enemy, 'health', 0),
            'target_max_health': getattr(target_enemy, 'max_health', 0),
            'success': damage > 0
        }
    
    def calculate_phaser_damage(self, attacker_ship, target_enemy, distance):
        """
        Calculate phaser damage without applying it to the target.
        
        Args:
            attacker_ship: Ship object with phaser system
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes between attacker and target
            
        Returns:
            dict: Combat calculation with damage amounts but target not modified
        """
        # Use the ship's phaser system for damage calculation
        damage = attacker_ship.phaser_system.fire(int(distance))
        
        # Determine range description for UI display
        if distance <= constants.PHASER_CLOSE_RANGE:
            range_description = "CLOSE RANGE"
        elif distance <= constants.PHASER_MEDIUM_RANGE:
            range_description = "MEDIUM RANGE"
        else:
            range_description = "LONG RANGE"
        
        # Initialize enemy attributes if they don't exist (for calculations only)
        current_shields = getattr(target_enemy, 'shields', constants.ENEMY_SHIELD_CAPACITY)
        max_shields = getattr(target_enemy, 'max_shields', constants.ENEMY_SHIELD_CAPACITY)
        current_health = getattr(target_enemy, 'health', constants.ENEMY_HULL_STRENGTH)
        max_health = getattr(target_enemy, 'max_health', constants.ENEMY_HULL_STRENGTH)
        
        # Calculate damage distribution without applying it
        damage_applied = 0
        shield_damage = 0
        hull_damage = 0
        target_destroyed = False
        
        if damage > 0:
            remaining_damage = damage
            
            # Calculate shield damage
            if current_shields > 0:
                shield_damage = min(remaining_damage, current_shields)
                remaining_damage -= shield_damage
            
            # Calculate hull damage
            if remaining_damage > 0 and (current_shields - shield_damage) <= 0:
                hull_damage = min(remaining_damage, current_health)
                remaining_damage -= hull_damage
            
            damage_applied = damage - remaining_damage
            target_destroyed = (current_health - hull_damage) <= 0
        
        # Return calculation result without modifying target
        return {
            'damage_calculated': damage,
            'damage_applied': damage_applied,
            'shield_damage': shield_damage,
            'hull_damage': hull_damage,
            'distance': distance,
            'range_description': range_description,
            'target_destroyed': target_destroyed,
            'target_shields_after': current_shields - shield_damage,
            'target_max_shields': max_shields,
            'target_health_after': current_health - hull_damage,
            'target_max_health': max_health,
            'success': True  # Always show effects if combat manager was called
        }
    
    def calculate_torpedo_damage(self, attacker_ship, target_enemy, distance):
        """
        Calculate torpedo damage without applying it to the target.
        
        Args:
            attacker_ship: Ship object with torpedo system
            target_enemy: Enemy map object or ship object to attack
            distance: Distance in hexes between attacker and target
            
        Returns:
            dict: Combat calculation similar to calculate_phaser_damage
        """
        # Use the ship's torpedo system
        damage = attacker_ship.torpedo_system.fire(int(distance))
        
        # Initialize enemy attributes if they don't exist (for calculations only)
        current_shields = getattr(target_enemy, 'shields', constants.ENEMY_SHIELD_CAPACITY)
        max_shields = getattr(target_enemy, 'max_shields', constants.ENEMY_SHIELD_CAPACITY)
        current_health = getattr(target_enemy, 'health', constants.ENEMY_HULL_STRENGTH)
        max_health = getattr(target_enemy, 'max_health', constants.ENEMY_HULL_STRENGTH)
        
        # Calculate damage distribution without applying it
        damage_applied = 0
        shield_damage = 0
        hull_damage = 0
        target_destroyed = False
        
        if damage > 0:
            remaining_damage = damage
            
            # Calculate shield damage
            if current_shields > 0:
                shield_damage = min(remaining_damage, current_shields)
                remaining_damage -= shield_damage
            
            # Calculate hull damage  
            if remaining_damage > 0 and (current_shields - shield_damage) <= 0:
                hull_damage = min(remaining_damage, current_health)
                remaining_damage -= hull_damage
            
            damage_applied = damage - remaining_damage
            target_destroyed = (current_health - hull_damage) <= 0
        
        # Return calculation result without modifying target
        return {
            'damage_calculated': damage,
            'damage_applied': damage_applied,
            'shield_damage': shield_damage,
            'hull_damage': hull_damage,
            'distance': distance,
            'target_destroyed': target_destroyed,
            'target_shields_after': current_shields - shield_damage,
            'target_max_shields': max_shields,
            'target_health_after': current_health - hull_damage,
            'target_max_health': max_health,
            'success': damage > 0
        }
    
    def apply_damage_to_enemy(self, target_enemy, combat_result):
        """
        Apply previously calculated damage to the target enemy.
        
        Args:
            target_enemy: Enemy map object to damage
            combat_result: Result from calculate_phaser_damage or calculate_torpedo_damage
            
        Returns:
            dict: Updated combat result with actual enemy status after damage
        """
        # Initialize enemy attributes if they don't exist
        if not hasattr(target_enemy, 'shields'):
            target_enemy.shields = constants.ENEMY_SHIELD_CAPACITY
        if not hasattr(target_enemy, 'max_shields'):
            target_enemy.max_shields = constants.ENEMY_SHIELD_CAPACITY
        if not hasattr(target_enemy, 'health'):
            target_enemy.health = constants.ENEMY_HULL_STRENGTH
        if not hasattr(target_enemy, 'max_health'):
            target_enemy.max_health = constants.ENEMY_HULL_STRENGTH
        
        # Apply the calculated damage
        if combat_result['shield_damage'] > 0:
            target_enemy.shields = max(0, target_enemy.shields - combat_result['shield_damage'])
        
        if combat_result['hull_damage'] > 0:
            target_enemy.health = max(0, target_enemy.health - combat_result['hull_damage'])
        
        # Update the combat result with actual final status
        updated_result = combat_result.copy()
        updated_result['target_shields'] = target_enemy.shields
        updated_result['target_health'] = target_enemy.health
        updated_result['target_destroyed'] = target_enemy.health <= 0
        
        return updated_result
    
    def calculate_distance(self, pos1, pos2):
        """
        Calculate hex grid distance between two positions.
        
        Args:
            pos1: Tuple of (q, r) coordinates
            pos2: Tuple of (q, r) coordinates
            
        Returns:
            float: Distance in hexes
        """
        import math
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.hypot(dx, dy)
    
    # Enemy AI Management Methods
    
    def get_or_create_enemy_ship(self, enemy_obj, player_ship):
        """Get existing enemy ship instance or create new one"""
        enemy_id = id(enemy_obj)
        
        if enemy_id not in self.enemy_ships:
            # Create new EnemyShip instance
            position = (enemy_obj.system_q, enemy_obj.system_r) if hasattr(enemy_obj, 'system_q') else (0, 0)
            self.enemy_ships[enemy_id] = EnemyShip(
                name="Klingon Warship",
                max_shield_strength=constants.ENEMY_SHIELD_CAPACITY,
                hull_strength=constants.ENEMY_HULL_STRENGTH,
                energy=1000,
                max_energy=1000,
                position=position
            )
            self.enemy_ships[enemy_id].set_target(player_ship)
        
        return self.enemy_ships[enemy_id]
    
    def update_enemy_ai(self, delta_time, systems, current_system, hex_grid, player_ship):
        """Update AI for all enemy ships in current system"""
        if current_system not in systems:
            return
        
        for obj in systems[current_system]:
            if obj.type == 'enemy' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                enemy_ship = self.get_or_create_enemy_ship(obj, player_ship)
                # Provide system objects for collision detection
                enemy_ship.set_system_objects(systems[current_system])
                enemy_ship.update_ai(delta_time)
                
                # Update enemy object position from ship's smooth animation
                render_pos = enemy_ship.get_render_position()
                # Convert hex coordinates to pixel coordinates and store for rendering
                pixel_x, pixel_y = hex_grid.get_hex_center(render_pos[0], render_pos[1])
                obj.anim_px = pixel_x
                obj.anim_py = pixel_y
                
                # Update logical hex position when enemy ship completes movement
                # This ensures right-click detection works at the new location
                if not enemy_ship.is_moving:
                    obj.system_q = int(enemy_ship.position[0])
                    obj.system_r = int(enemy_ship.position[1])
    
    def cleanup_enemy_ships(self, systems, current_system):
        """Remove enemy ship instances for enemies that no longer exist"""
        if current_system not in systems:
            return
            
        # Get current enemy object IDs in the system
        current_enemy_ids = set()
        for obj in systems[current_system]:
            if obj.type == 'enemy':
                current_enemy_ids.add(id(obj))
        
        # Remove enemy ships that are no longer in the system
        to_remove = []
        for enemy_id in self.enemy_ships:
            if enemy_id not in current_enemy_ids:
                to_remove.append(enemy_id)
        
        for enemy_id in to_remove:
            del self.enemy_ships[enemy_id]