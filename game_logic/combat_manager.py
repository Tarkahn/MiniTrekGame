"""
Combat Manager - Handles combat-related game logic for player weapons only
Enemy ships are purely static decorative objects
"""

import time
import random
from data import constants
from ship.enemy_ship import EnemyShip


class CombatManager:
    """
    Manages combat interactions for player weapons only.
    Enemy ships are static and do not participate in combat.
    """

    def __init__(self):
        self.enemy_ships = {}  # Maps enemy object ID to static EnemyShip instances
        self.weapon_animation_manager = None  # Will be set by game initialization

    def calculate_phaser_damage(self, attacker, target, distance):
        """
        Calculate phaser damage based on range, power allocation, and target defenses.

        Args:
            attacker: Ship firing phasers
            target: Target enemy object (with health, shields, etc.)
            distance: Distance to target in hexes

        Returns:
            Dict with combat result including damage amounts and success status
        """
        # Calculate base damage using power allocation
        phaser_power = attacker.power_allocation.get('phasers', 5)
        base_damage = phaser_power * constants.PHASER_DAMAGE_PER_POWER_LEVEL

        # Apply phaser system damage modifier
        damage_modifier = 1.0
        if hasattr(attacker, 'get_phaser_damage_multiplier'):
            damage_modifier = attacker.get_phaser_damage_multiplier()
            base_damage = int(base_damage * damage_modifier)

        # Apply range penalty
        if distance > constants.PHASER_RANGE:
            print(f"[PHASER] Target out of range: distance={distance}, max_range={constants.PHASER_RANGE}")
            return {'success': False, 'message': 'Target out of phaser range', 'damage': 0}

        # Range penalty: damage per hex distance
        range_penalty = distance * constants.PHASER_RANGE_PENALTY
        final_damage = max(0, base_damage - range_penalty)

        print(f"[PHASER] Damage calc: power={phaser_power}, base={base_damage}, distance={distance}, range_penalty={range_penalty}, final={final_damage}")

        return {
            'success': True,
            'damage': final_damage,
            'damage_calculated': final_damage,
            'base_damage': base_damage,
            'range_penalty': range_penalty,
            'distance': distance
        }

    def calculate_torpedo_damage(self, attacker, target, distance):
        """
        Calculate torpedo damage. Torpedoes have fixed damage but limited quantity.

        Args:
            attacker: Ship firing torpedoes
            target: Target enemy object
            distance: Distance to target in hexes

        Returns:
            Dict with combat result including damage and success status
        """
        # Check if player has torpedoes
        if attacker.torpedo_count <= 0:
            return {'success': False, 'message': 'No torpedoes remaining', 'damage': 0}

        # Torpedoes have much longer range than phasers
        if distance > constants.TORPEDO_RANGE:
            return {'success': False, 'message': 'Target out of torpedo range', 'damage': 0}

        # Torpedoes do fixed damage
        torpedo_damage = constants.TORPEDO_DAMAGE

        print(f"[TORPEDO] Damage calc: distance={distance}, damage={torpedo_damage}")

        return {
            'success': True,
            'damage': torpedo_damage,
            'damage_calculated': torpedo_damage,
            'distance': distance,
            'torpedoes_remaining': attacker.torpedo_count - 1
        }

    def apply_damage_to_enemy(self, target_enemy, combat_result):
        """
        Apply calculated damage to an enemy using the same damage system as the player.
        Uses BaseShip.apply_damage for shield absorption, critical hits, cascading damage, etc.

        Args:
            target_enemy: Enemy object to damage (EnemyShip instance)
            combat_result: Result from calculate_*_damage function

        Returns:
            Updated combat result with final enemy status
        """
        damage = combat_result.get('damage', 0)

        # Debug: Print incoming damage
        target_name = getattr(target_enemy, 'name', 'Unknown')
        print(f"[COMBAT] apply_damage_to_enemy called for {target_name} with damage={damage}")

        # Track shield and hull before damage for reporting
        initial_shields = 0
        initial_hull = 0

        if hasattr(target_enemy, 'shield_system'):
            # Get shield capacity based on power level and integrity
            shield_power = target_enemy.shield_system.current_power_level
            shield_integrity = target_enemy.shield_system.current_integrity
            initial_shields = int((shield_power * target_enemy.shield_system.absorption_per_level) * (shield_integrity / 100.0))
            print(f"[COMBAT] Shield system found: power={shield_power}, integrity={shield_integrity}, effective_shields={initial_shields}")
        elif hasattr(target_enemy, 'shields'):
            initial_shields = target_enemy.shields
            print(f"[COMBAT] Using shields property: {initial_shields}")

        if hasattr(target_enemy, 'hull_strength'):
            initial_hull = target_enemy.hull_strength
        elif hasattr(target_enemy, 'health'):
            initial_hull = target_enemy.health

        # Use the proper apply_damage method from BaseShip if available
        # This handles shield absorption, critical hits, cascading damage, etc.
        if damage > 0 and hasattr(target_enemy, 'apply_damage'):
            # Use the full damage system (same as player ship)
            target_enemy.apply_damage(damage)
        elif damage > 0:
            # Fallback for objects without apply_damage (legacy MapObjects)
            shield_damage_legacy = min(damage, target_enemy.shields) if hasattr(target_enemy, 'shields') else 0
            hull_damage_legacy = damage - shield_damage_legacy

            if hasattr(target_enemy, 'shields'):
                target_enemy.shields -= shield_damage_legacy
            if hasattr(target_enemy, 'health'):
                target_enemy.health -= hull_damage_legacy
                target_enemy.health = max(0, target_enemy.health)

        # Get final values after damage
        final_shields = 0
        final_hull = 0

        if hasattr(target_enemy, 'shield_system'):
            shield_power = target_enemy.shield_system.current_power_level
            shield_integrity = target_enemy.shield_system.current_integrity
            final_shields = int((shield_power * target_enemy.shield_system.absorption_per_level) * (shield_integrity / 100.0))
        elif hasattr(target_enemy, 'shields'):
            final_shields = target_enemy.shields

        if hasattr(target_enemy, 'hull_strength'):
            final_hull = target_enemy.hull_strength
        elif hasattr(target_enemy, 'health'):
            final_hull = target_enemy.health

        # Calculate actual damage dealt for reporting
        shield_damage = max(0, initial_shields - final_shields)
        hull_damage = max(0, initial_hull - final_hull)

        # Sync the compatibility properties (shields/health) with actual ship state
        if hasattr(target_enemy, '_shields') and hasattr(target_enemy, 'shield_system'):
            target_enemy._shields = final_shields
        if hasattr(target_enemy, '_health') and hasattr(target_enemy, 'hull_strength'):
            target_enemy._health = target_enemy.hull_strength

        # Always update the combat result with damage fields (even when 0)
        updated_result = combat_result.copy()
        updated_result['shield_damage'] = shield_damage
        updated_result['hull_damage'] = hull_damage
        updated_result['target_shields'] = final_shields
        updated_result['target_health'] = final_hull
        updated_result['target_max_health'] = target_enemy.max_hull_strength if hasattr(target_enemy, 'max_hull_strength') else 100
        updated_result['target_max_shields'] = target_enemy.max_shields if hasattr(target_enemy, 'max_shields') else 100
        updated_result['target_destroyed'] = final_hull <= 0

        return updated_result

    def get_or_create_enemy_ship(self, enemy_obj, player_ship):
        """Get existing static enemy ship instance or create new one"""
        enemy_id = id(enemy_obj)

        if enemy_id not in self.enemy_ships:
            # Create new dynamic EnemyShip instance with faction-based personality
            position = (enemy_obj.system_q, enemy_obj.system_r) if hasattr(enemy_obj, 'system_q') else (0, 0)

            # Get faction from enemy object (defaults to klingon for backwards compatibility)
            faction = getattr(enemy_obj, 'faction', None) or 'klingon'

            # Generate faction-appropriate name
            if faction == 'romulan':
                ship_name = f"Romulan Warbird R-{enemy_id % 1000}"
            else:
                ship_name = f"Klingon Warship K-{enemy_id % 1000}"

            self.enemy_ships[enemy_id] = EnemyShip(
                name=ship_name,
                max_shield_strength=constants.ENEMY_SHIELD_CAPACITY,
                hull_strength=constants.ENEMY_HULL_STRENGTH,
                energy=1000,
                max_energy=1000,
                position=position,
                faction=faction
            )

        return self.enemy_ships[enemy_id]
    
    def update_enemy_ai(self, delta_time, systems, current_system, hex_grid, player_ship):
        """Update dynamic Klingon AI for all enemies in current system"""
        if current_system not in systems:
            return
            
        # Find all enemy objects in the current system
        enemy_objects = [obj for obj in systems[current_system] if obj.type == 'enemy']
        
        if not enemy_objects:
            return
        
            
        for enemy_obj in enemy_objects:
            # Get or create the EnemyShip instance for this enemy
            enemy_ship = self.get_or_create_enemy_ship(enemy_obj, player_ship)
            
            # Set the player as the target
            enemy_ship.set_target(player_ship)
            
            # Provide system awareness for tactical decisions
            enemy_ship.set_system_objects(systems[current_system])
            
            # Update the AI
            enemy_ship.update_ai(delta_time)
            
            # Sync the MapObject position with the EnemyShip position
            # Ensure enemy ships are always positioned on hex centers
            current_position = enemy_ship.get_render_position()
            enemy_obj.system_q = int(round(current_position[0]))
            enemy_obj.system_r = int(round(current_position[1]))
            
            # Process any weapon animations the enemy wants to fire
            weapon_animations = enemy_ship.get_pending_weapon_animations()
            for animation in weapon_animations:
                # Start visual/audio weapon animation using animation manager
                # Pass system_objects so we can find the player's actual system position
                self._start_enemy_weapon_animation(animation, enemy_ship, player_ship, hex_grid, systems[current_system])
    
    def cleanup_enemy_ships(self, systems, current_system):
        """Remove enemy ship instances for enemies that no longer exist"""
        if current_system not in systems:
            return
            
        # Get all current enemy object IDs in the system
        current_enemy_ids = set()
        for obj in systems[current_system]:
            if obj.type == 'enemy':
                current_enemy_ids.add(id(obj))
        
        # Remove enemy ships that no longer exist
        enemy_ids_to_remove = []
        for enemy_id in self.enemy_ships:
            if enemy_id not in current_enemy_ids:
                enemy_ids_to_remove.append(enemy_id)
        
        for enemy_id in enemy_ids_to_remove:
            del self.enemy_ships[enemy_id]
    
    def _start_enemy_weapon_animation(self, weapon_animation, enemy_ship, player_ship, hex_grid, system_objects=None):
        """Start visual/audio weapon animation using the weapon animation manager"""
        if not self.weapon_animation_manager:
            return  # No animation manager available

        weapon_power = weapon_animation.get('power', 5)
        weapon_type = weapon_animation.get('type', 'disruptor')

        # Calculate damage based on weapon power
        base_damage = int(weapon_power * 3)  # Increased damage for more visible effects

        # Convert hex positions to pixel positions for animation using proper hex grid
        enemy_pos = enemy_ship.get_render_position()

        # Get player's SYSTEM position (not sector position)
        # The player's system position is stored on the player MapObject, not player_ship
        player_system_pos = None
        if system_objects:
            for obj in system_objects:
                if obj.type == 'player' and hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                    player_system_pos = (obj.system_q, obj.system_r)
                    break

        # Fallback to player_ship.position if we can't find the player object
        # (this would be wrong but better than crashing)
        if player_system_pos is None:
            player_system_pos = player_ship.position

        # Use proper hex-to-pixel conversion
        enemy_pixel_pos = hex_grid.get_hex_center(enemy_pos[0], enemy_pos[1])
        player_pixel_pos = hex_grid.get_hex_center(player_system_pos[0], player_system_pos[1])
        
        # Start the appropriate weapon animation
        if weapon_type == 'torpedo':
            self.weapon_animation_manager.enemy_fire_torpedo(
                enemy_ship, enemy_pixel_pos, player_pixel_pos, base_damage
            )
        elif weapon_type == 'disruptor' or weapon_type == 'phaser':
            self.weapon_animation_manager.enemy_fire_phaser(
                enemy_ship, enemy_pixel_pos, player_pixel_pos, base_damage, weapon_type
            )
    
    def set_weapon_animation_manager(self, manager):
        """Set the weapon animation manager reference"""
        self.weapon_animation_manager = manager