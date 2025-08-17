from .base_ship import BaseShip
from data import constants
from ship.ship_systems.phaser import Phaser
from ship.ship_systems.torpedo import Torpedo
from ship.ship_systems.shield import Shield
import random
import time
import math


class EnemyShip(BaseShip):
    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy, weapons=None, position=None):
        enemy_shield = Shield(max_shield_strength, self)
        super().__init__(name, enemy_shield, hull_strength, energy, max_energy, weapons, position)
        self.target = None
        self.aggression_level = "medium"  # Can be "low", "medium", "high"
        self.pursuit_range = 500
        self.attack_range = 200
        self.phaser_system = Phaser(power=constants.ENEMY_PHASER_POWER, range=constants.ENEMY_PHASER_RANGE, ship=self)  # Example values
        self.torpedo_system = Torpedo(power=constants.ENEMY_TORPEDO_POWER, speed=constants.ENEMY_TORPEDO_SPEED, accuracy=constants.ENEMY_TORPEDO_ACCURACY, ship=self)  # Example values
        
        # Generate comprehensive personality parameters
        self.personality = self._generate_personality()
        
        # Movement personality parameters (enhanced)
        self.movement_speed = self.personality['movement_speed_base']  # Speed multiplier
        self.movement_distance = self.personality['movement_distance_pref']  # Distance before changing direction
        self.dwell_time = random.uniform(1.5, 4.0)  # Time to stay at location (seconds)
        self.maneuverability = self.personality['movement_frequency']  # How often to change direction
        
        # Combat personality parameters
        self.attack_frequency = self.personality['attack_frequency']  # Seconds between attacks
        self.weapon_preference = self.personality['weapon_preference']  # 0.0=phasers, 1.0=torpedoes
        self.range_preference = self.personality['range_preference']  # Preferred engagement distance
        self.combat_posture = self.personality['combat_posture']  # defensive/balanced/aggressive/berserker
        self.evasion_tendency = self.personality['evasion_tendency']  # Likelihood to evade when damaged
        self.pursuit_aggressiveness = self.personality['pursuit_aggressiveness']  # How aggressively to pursue
        self.retreat_threshold = self.personality['retreat_threshold']  # Hull % when enemy retreats
        
        # Novel personality parameters
        self.adaptation_rate = self.personality['adaptation_rate']  # How quickly enemy learns
        self.desperation_modifier = self.personality['desperation_modifier']  # Damage multiplier when damaged
        self.coordination_level = self.personality['coordination_level']  # Works with other enemies
        self.surprise_factor = self.personality['surprise_factor']  # Chance for unexpected moves
        
        # Combat state tracking
        self.last_attack_time = 0
        self.consecutive_hits_taken = 0
        self.player_pattern_memory = []  # Track player behavior for adaptation
        self.is_retreating = False
        self.desperation_active = False
        
        # Reduce dwell time for more active movement
        self.dwell_time = min(self.dwell_time, 2.0)  # Cap at 2 seconds max
        
        # Debug output for personality
        print(f"[ENEMY AI] {self.name} spawned: {self.get_personality_description()}")
        
        # Movement state
        self.current_destination = None
        self.movement_start_time = None
        self.last_decision_time = time.time()
        # Choose movement pattern based on personality weights
        patterns = ['patrol', 'circular', 'evasive']
        weights = self.personality['movement_pattern_weights']
        self.movement_pattern = random.choices(patterns, weights=weights)[0]
        self.patrol_points = []
        self.patrol_index = 0
        
        # Ensure initial position is constrained to grid
        if position:
            constrained_pos = self._constrain_to_grid_bounds(position[0], position[1])
            self.position = constrained_pos
        else:
            self.position = (10, 10)  # Default to center of 20x20 grid
        
        # Animation state for smooth movement (hex coordinates)
        self.anim_x = self.position[0]
        self.anim_y = self.position[1]
        self.is_moving = False
        self.move_progress = 0.0

    def _constrain_to_grid_bounds(self, q, r, grid_size=20):
        """Helper method to constrain coordinates during initialization"""
        q_constrained = max(0, min(grid_size - 1, int(round(q))))
        r_constrained = max(0, min(grid_size - 1, int(round(r))))
        return (q_constrained, r_constrained)
    
    def _generate_personality(self):
        """Generate comprehensive personality parameters for unique enemy encounters"""
        # Choose a random archetype with some having higher probability
        archetypes = ['predator', 'sniper', 'berserker', 'tactician', 'coward', 'veteran', 'random']
        archetype_weights = [0.2, 0.15, 0.1, 0.15, 0.1, 0.1, 0.2]  # Predator and random more common
        archetype = random.choices(archetypes, weights=archetype_weights)[0]
        
        if archetype == 'predator':
            return self._create_predator_personality()
        elif archetype == 'sniper':
            return self._create_sniper_personality()
        elif archetype == 'berserker':
            return self._create_berserker_personality()
        elif archetype == 'tactician':
            return self._create_tactician_personality()
        elif archetype == 'coward':
            return self._create_coward_personality()
        elif archetype == 'veteran':
            return self._create_veteran_personality()
        else:  # random
            return self._create_random_personality()
    
    def _create_predator_personality(self):
        """Aggressive pursuer that likes close combat"""
        return {
            'archetype': 'predator',
            'movement_frequency': random.uniform(0.7, 1.0),  # High movement frequency
            'movement_speed_base': random.uniform(1.2, 1.8),  # Fast movement
            'movement_distance_pref': random.uniform(2.0, 4.0),  # Short, aggressive movements
            'movement_pattern_weights': [0.1, 0.2, 0.7],  # Prefer evasive (hunting) pattern
            'attack_frequency': random.uniform(0.5, 1.5),  # Very frequent attacks
            'weapon_preference': random.uniform(0.0, 0.3),  # Prefer phasers for close combat
            'range_preference': random.uniform(2.0, 6.0),  # Close range preference
            'combat_posture': 'aggressive',
            'evasion_tendency': random.uniform(0.1, 0.3),  # Low evasion, aggressive
            'pursuit_aggressiveness': random.uniform(0.8, 1.0),  # High pursuit
            'retreat_threshold': random.uniform(0.1, 0.25),  # Fight to near death
            'adaptation_rate': random.uniform(0.3, 0.6),  # Moderate adaptation
            'desperation_modifier': random.uniform(1.5, 2.2),  # High desperation damage
            'coordination_level': random.uniform(0.2, 0.5),  # Some coordination
            'surprise_factor': random.uniform(0.1, 0.2)  # Some unpredictability
        }
    
    def _create_sniper_personality(self):
        """Long-range fighter that maintains distance"""
        return {
            'archetype': 'sniper',
            'movement_frequency': random.uniform(0.3, 0.6),  # Moderate movement
            'movement_speed_base': random.uniform(0.8, 1.2),  # Normal speed
            'movement_distance_pref': random.uniform(4.0, 7.0),  # Long movements for positioning
            'movement_pattern_weights': [0.6, 0.3, 0.1],  # Prefer patrol patterns
            'attack_frequency': random.uniform(1.0, 2.5),  # Moderate attack rate
            'weapon_preference': random.uniform(0.7, 1.0),  # Heavy torpedo preference
            'range_preference': random.uniform(8.0, 15.0),  # Long range engagement
            'combat_posture': 'defensive',
            'evasion_tendency': random.uniform(0.6, 0.8),  # High evasion
            'pursuit_aggressiveness': random.uniform(0.1, 0.4),  # Low pursuit
            'retreat_threshold': random.uniform(0.4, 0.7),  # Retreat when moderately damaged
            'adaptation_rate': random.uniform(0.4, 0.7),  # Good adaptation
            'desperation_modifier': random.uniform(1.0, 1.3),  # Low desperation bonus
            'coordination_level': random.uniform(0.5, 0.8),  # Good coordination
            'surprise_factor': random.uniform(0.05, 0.15)  # Low surprise factor
        }
    
    def _create_berserker_personality(self):
        """Reckless all-out attacker"""
        return {
            'archetype': 'berserker',
            'movement_frequency': random.uniform(0.8, 1.0),  # Constant movement
            'movement_speed_base': random.uniform(1.5, 2.0),  # Very fast
            'movement_distance_pref': random.uniform(1.0, 3.0),  # Short, erratic movements
            'movement_pattern_weights': [0.1, 0.1, 0.8],  # Highly evasive/erratic
            'attack_frequency': random.uniform(0.3, 1.0),  # Extremely frequent attacks
            'weapon_preference': random.uniform(0.4, 0.6),  # Mixed weapons
            'range_preference': random.uniform(1.0, 4.0),  # Very close range
            'combat_posture': 'berserker',
            'evasion_tendency': random.uniform(0.0, 0.2),  # Almost no evasion
            'pursuit_aggressiveness': random.uniform(0.9, 1.0),  # Maximum pursuit
            'retreat_threshold': random.uniform(0.05, 0.15),  # Fight to the death
            'adaptation_rate': random.uniform(0.1, 0.3),  # Poor adaptation
            'desperation_modifier': random.uniform(2.0, 2.5),  # Maximum desperation
            'coordination_level': random.uniform(0.0, 0.2),  # Poor coordination
            'surprise_factor': random.uniform(0.2, 0.3)  # High unpredictability
        }
    
    def _create_tactician_personality(self):
        """Balanced fighter that adapts and coordinates"""
        return {
            'archetype': 'tactician',
            'movement_frequency': random.uniform(0.5, 0.8),  # Thoughtful movement
            'movement_speed_base': random.uniform(1.0, 1.4),  # Good speed
            'movement_distance_pref': random.uniform(3.0, 6.0),  # Tactical positioning
            'movement_pattern_weights': [0.4, 0.4, 0.2],  # Balanced patterns
            'attack_frequency': random.uniform(1.0, 2.0),  # Measured attacks
            'weapon_preference': random.uniform(0.3, 0.7),  # Situational weapon choice
            'range_preference': random.uniform(4.0, 10.0),  # Medium range
            'combat_posture': 'balanced',
            'evasion_tendency': random.uniform(0.4, 0.7),  # Moderate evasion
            'pursuit_aggressiveness': random.uniform(0.4, 0.7),  # Tactical pursuit
            'retreat_threshold': random.uniform(0.3, 0.5),  # Strategic retreat
            'adaptation_rate': random.uniform(0.7, 1.0),  # High adaptation
            'desperation_modifier': random.uniform(1.2, 1.6),  # Moderate desperation
            'coordination_level': random.uniform(0.7, 1.0),  # High coordination
            'surprise_factor': random.uniform(0.15, 0.25)  # Tactical surprises
        }
    
    def _create_coward_personality(self):
        """Defensive fighter that avoids confrontation"""
        return {
            'archetype': 'coward',
            'movement_frequency': random.uniform(0.7, 1.0),  # Frequent evasive movement
            'movement_speed_base': random.uniform(1.1, 1.6),  # Fast escape speed
            'movement_distance_pref': random.uniform(4.0, 8.0),  # Long evasive movements
            'movement_pattern_weights': [0.2, 0.1, 0.7],  # Highly evasive
            'attack_frequency': random.uniform(2.0, 4.0),  # Opportunistic attacks
            'weapon_preference': random.uniform(0.8, 1.0),  # Long-range torpedoes
            'range_preference': random.uniform(10.0, 18.0),  # Maximum range
            'combat_posture': 'defensive',
            'evasion_tendency': random.uniform(0.8, 1.0),  # Maximum evasion
            'pursuit_aggressiveness': random.uniform(0.0, 0.2),  # No pursuit
            'retreat_threshold': random.uniform(0.6, 0.9),  # Retreat early
            'adaptation_rate': random.uniform(0.2, 0.5),  # Poor adaptation (panicked)
            'desperation_modifier': random.uniform(0.8, 1.1),  # Lower damage when panicked
            'coordination_level': random.uniform(0.1, 0.4),  # Poor coordination
            'surprise_factor': random.uniform(0.0, 0.1)  # Predictable
        }
    
    def _create_veteran_personality(self):
        """Experienced balanced fighter with high adaptability"""
        return {
            'archetype': 'veteran',
            'movement_frequency': random.uniform(0.6, 0.9),  # Experienced movement
            'movement_speed_base': random.uniform(1.1, 1.5),  # Good speed
            'movement_distance_pref': random.uniform(3.0, 7.0),  # Flexible positioning
            'movement_pattern_weights': [0.35, 0.35, 0.3],  # Balanced patterns
            'attack_frequency': random.uniform(0.8, 2.0),  # Variable attack timing
            'weapon_preference': random.uniform(0.2, 0.8),  # Flexible weapon choice
            'range_preference': random.uniform(3.0, 12.0),  # Flexible range
            'combat_posture': 'balanced',
            'evasion_tendency': random.uniform(0.5, 0.8),  # Good evasion
            'pursuit_aggressiveness': random.uniform(0.4, 0.8),  # Flexible pursuit
            'retreat_threshold': random.uniform(0.25, 0.45),  # Strategic retreat
            'adaptation_rate': random.uniform(0.8, 1.0),  # Maximum adaptation
            'desperation_modifier': random.uniform(1.3, 1.8),  # Good desperation fighting
            'coordination_level': random.uniform(0.6, 0.9),  # High coordination
            'surprise_factor': random.uniform(0.2, 0.3)  # Unpredictable tactics
        }
    
    def _create_random_personality(self):
        """Completely randomized personality for maximum variety"""
        return {
            'archetype': 'random',
            'movement_frequency': random.uniform(0.2, 1.0),
            'movement_speed_base': random.uniform(0.6, 2.0),
            'movement_distance_pref': random.uniform(1.0, 8.0),
            'movement_pattern_weights': [random.uniform(0.1, 0.8), random.uniform(0.1, 0.8), random.uniform(0.1, 0.8)],
            'attack_frequency': random.uniform(0.5, 3.0),
            'weapon_preference': random.uniform(0.0, 1.0),
            'range_preference': random.uniform(1.0, 18.0),
            'combat_posture': random.choice(['defensive', 'balanced', 'aggressive', 'berserker']),
            'evasion_tendency': random.uniform(0.0, 1.0),
            'pursuit_aggressiveness': random.uniform(0.0, 1.0),
            'retreat_threshold': random.uniform(0.1, 0.9),
            'adaptation_rate': random.uniform(0.0, 1.0),
            'desperation_modifier': random.uniform(0.8, 2.5),
            'coordination_level': random.uniform(0.0, 1.0),
            'surprise_factor': random.uniform(0.0, 0.3)
        }

    def set_target(self, target):
        self.target = target
    
    def set_system_objects(self, system_objects):
        """Set reference to all objects in the current system for collision detection"""
        self.system_objects = system_objects

    def update_ai(self, delta_time):
        """Update AI logic including movement and combat decisions"""
        current_time = time.time()
        
        # Update smooth movement animation
        self.update_movement_animation(delta_time)
        
        # Make movement decisions
        self.update_movement_decisions(current_time)
        
        # Personality-driven combat AI 
        if self.target and hasattr(self.target, 'is_alive') and self.target.is_alive():
            # Add debug output to verify combat AI is running
            if not hasattr(self, '_last_combat_debug') or current_time - self._last_combat_debug > 5.0:
                print(f"[COMBAT DEBUG] {self.name} updating combat AI - target at distance {self.calculate_distance(self.target.position):.1f}")
                self._last_combat_debug = current_time
            self.update_combat_ai(current_time)
        else:
            # Debug why combat isn't running
            if not hasattr(self, '_last_target_debug') or current_time - self._last_target_debug > 5.0:
                print(f"[TARGET DEBUG] {self.name} - target: {self.target}, has target: {self.target is not None}")
                if self.target:
                    print(f"[TARGET DEBUG] - target has is_alive: {hasattr(self.target, 'is_alive')}")
                    if hasattr(self.target, 'is_alive'):
                        print(f"[TARGET DEBUG] - target is alive: {self.target.is_alive()}")
                self._last_target_debug = current_time
    
    def update_combat_ai(self, current_time):
        """Comprehensive personality-driven combat AI system"""
        if not self.target or not hasattr(self.target, 'position'):
            return
            
        distance_to_target = self.calculate_distance(self.target.position)
        
        # Check if enemy should retreat based on hull damage and personality
        current_hull_ratio = self.hull_strength / self.max_hull_strength
        if current_hull_ratio <= self.retreat_threshold and not self.is_retreating:
            self.is_retreating = True
            print(f"{self.name} ({self.personality['archetype']}) is retreating!")
            
        # Activate desperation mode when heavily damaged
        if current_hull_ratio <= 0.3 and not self.desperation_active:
            self.desperation_active = True
            print(f"{self.name} ({self.personality['archetype']}) enters desperation mode!")
        
        # Retreating behavior - try to escape
        if self.is_retreating:
            self.retreat_behavior(distance_to_target)
            return
            
        # Determine if enemy should engage in combat
        should_attack = self.should_attack(current_time, distance_to_target)
        should_pursue = self.should_pursue(distance_to_target)
        should_evade = self.should_evade(distance_to_target)
        
        # Combat decision priority: evade -> attack -> pursue -> patrol
        if should_evade:
            self.evasive_maneuver(distance_to_target)
        elif should_attack:
            self.execute_attack(distance_to_target, current_time)
        elif should_pursue:
            self.pursue_target()
        # Otherwise continue normal movement patterns
    
    def should_attack(self, current_time, distance_to_target):
        """Determine if enemy should attack based on personality and conditions"""
        # Check attack cooldown based on personality
        time_since_attack = current_time - self.last_attack_time
        if time_since_attack < self.attack_frequency:
            return False
        
        # Range check based on weapon preference and personality
        in_weapon_range = False
        if self.weapon_preference < 0.5:  # Prefer phasers
            # Can use phasers OR fall back to torpedoes if out of phaser range
            in_weapon_range = (distance_to_target <= self.phaser_system.range or 
                             distance_to_target <= 15)  # Torpedo fallback
        else:  # Prefer torpedoes
            in_weapon_range = distance_to_target <= 15  # Torpedo max range
            
        # Personality-based range preference - be more flexible for engagement
        in_preferred_range = distance_to_target <= max(self.range_preference, 10)
        
        # Combat posture affects attack likelihood (made more aggressive)
        posture_modifier = {
            'defensive': 0.6,   # Increased from 0.3 to 0.6
            'balanced': 0.8,    # Increased from 0.7 to 0.8
            'aggressive': 0.95, # Increased from 0.9 to 0.95
            'berserker': 1.0
        }.get(self.combat_posture, 0.8)
        
        # Surprise factor - random unexpected attacks
        surprise_attack = random.random() < self.surprise_factor
        
        return (in_weapon_range and in_preferred_range and random.random() < posture_modifier) or surprise_attack
    
    def should_pursue(self, distance_to_target):
        """Determine if enemy should pursue player based on personality"""
        # Don't pursue if too close (prefer to attack) or too far (out of interest)
        if distance_to_target < self.range_preference * 0.5:
            return False
        # Increased max pursuit range - enemies will chase much further
        if distance_to_target > max(15, self.range_preference * 4.0):
            return False
            
        # Pursuit based on personality
        return random.random() < self.pursuit_aggressiveness
    
    def should_evade(self, distance_to_target):
        """Determine if enemy should perform evasive maneuvers"""
        # Only evade when VERY close to player (much more restrictive)
        very_close_to_player = distance_to_target < 3.0  # Fixed close distance instead of percentage
        under_fire = self.consecutive_hits_taken > 0  # Track if recently hit by player
        
        # Much reduced evasion chance - prioritize combat over evasion
        evasion_chance = self.evasion_tendency * 0.2  # Further reduced base evasion
        if very_close_to_player:
            evasion_chance *= 2.0  # Only double when very close
        if under_fire:
            evasion_chance *= 1.2  # Slight increase when under fire
        if self.desperation_active:
            evasion_chance *= 0.1  # Almost no evasion when desperate
            
        return random.random() < min(evasion_chance, 0.4)  # Cap at 40% max evasion
    
    def execute_attack(self, distance_to_target, current_time):
        """Execute attack based on weapon preference and personality"""
        self.last_attack_time = current_time
        
        # Choose weapon based on preference and tactical situation
        use_torpedoes = False
        if self.weapon_preference > 0.5:  # Prefer torpedoes
            use_torpedoes = distance_to_target > 3 and self.has_torpedoes()
        else:  # Prefer phasers
            use_torpedoes = distance_to_target > self.phaser_system.range and self.has_torpedoes()
        
        # Tactical weapon switching for tactician archetype
        if self.personality['archetype'] == 'tactician':
            if distance_to_target < 4:
                use_torpedoes = False  # Use phasers for close combat
            elif not self.target.shield_system.current_power_level > 0:
                use_torpedoes = True  # Use torpedoes against unshielded targets
        
        # Apply desperation modifier to damage
        if use_torpedoes:
            damage = self.fire_torpedoes_at_target(distance_to_target)
        else:
            damage = self.fire_phasers_at_target(distance_to_target)
            
        if damage > 0 and self.desperation_active:
            # Note: Actual damage application would need to be modified in weapon systems
            print(f"{self.name} desperate attack! (x{self.desperation_modifier:.1f} personality modifier)")
    
    def fire_phasers_at_target(self, distance_to_target):
        """Fire phasers with personality-based power allocation"""
        if distance_to_target > self.phaser_system.range or self.phaser_system.is_on_cooldown():
            return 0
            
        # Allocate phaser power based on combat posture
        power_allocation = {
            'defensive': random.randint(3, 6),
            'balanced': random.randint(4, 7),
            'aggressive': random.randint(6, 8),
            'berserker': random.randint(7, 9)
        }.get(self.combat_posture, 5)
        
        # Apply power allocation to ship's systems
        self.allocate_power('phasers', power_allocation)
        
        damage = self.phaser_system.fire(distance_to_target)
        if damage > 0:
            # Use weapon animation system instead of direct damage
            self._trigger_weapon_animation('phaser', distance_to_target, damage)
            print(f"{self.name} ({self.personality['archetype']}) fires phasers at {power_allocation} power! Damage: {damage}")
        return damage
    
    def fire_torpedoes_at_target(self, distance_to_target):
        """Fire torpedoes at target"""
        if not self.has_torpedoes() or self.torpedo_system.is_on_cooldown():
            return 0
            
        damage = self.torpedo_system.fire(distance_to_target)
        if damage > 0:
            # Use weapon animation system instead of direct damage
            self._trigger_weapon_animation('torpedo', distance_to_target, damage)
            print(f"{self.name} ({self.personality['archetype']}) fires torpedo! Damage: {damage}")
        return damage
    
    def evasive_maneuver(self, distance_to_target):
        """Perform evasive movement to avoid player attacks"""
        if self.is_moving:
            return  # Already moving
            
        # Evasive movement away from player
        current_x, current_y = self.position
        target_x, target_y = self.target.position
        
        # Calculate direction away from player
        dx = current_x - target_x
        dy = current_y - target_y
        
        # Normalize and scale by evasion distance
        distance = math.hypot(dx, dy)
        if distance > 0:
            evasion_distance = min(self.movement_distance * 0.7, 3)  # Quick evasive moves
            evade_x = current_x + (dx / distance) * evasion_distance
            evade_y = current_y + (dy / distance) * evasion_distance
            
            # Add some randomness for unpredictability
            evade_x += random.uniform(-1, 1)
            evade_y += random.uniform(-1, 1)
            
            self.set_destination((evade_x, evade_y))
    
    def retreat_behavior(self, distance_to_target):
        """Retreat behavior when hull is critically damaged"""
        if self.is_moving:
            return
            
        # Move away from player toward map edges
        current_x, current_y = self.position
        target_x, target_y = self.target.position
        
        # Direction away from player
        dx = current_x - target_x  
        dy = current_y - target_y
        
        # Head toward nearest map edge
        to_left = current_x
        to_right = 19 - current_x
        to_top = current_y
        to_bottom = 19 - current_y
        
        min_edge = min(to_left, to_right, to_top, to_bottom)
        
        if min_edge == to_left:
            retreat_x, retreat_y = 0, current_y
        elif min_edge == to_right:
            retreat_x, retreat_y = 19, current_y
        elif min_edge == to_top:
            retreat_x, retreat_y = current_x, 0
        else:
            retreat_x, retreat_y = current_x, 19
            
        self.set_destination((retreat_x, retreat_y))

    def update_movement_animation(self, delta_time):
        """Update smooth movement animation similar to player ship"""
        if self.is_moving and self.current_destination:
            # Calculate movement progress
            move_duration = 2.0 / self.movement_speed  # Base 2 seconds adjusted by speed
            if self.movement_start_time is None:
                self.movement_start_time = time.time()
            
            elapsed = time.time() - self.movement_start_time
            self.move_progress = min(elapsed / move_duration, 1.0)
            
            # Interpolate position
            start_x, start_y = self.position
            dest_x, dest_y = self.current_destination
            
            self.anim_x = start_x + (dest_x - start_x) * self.move_progress
            self.anim_y = start_y + (dest_y - start_y) * self.move_progress
            
            # Check if arrived
            if self.move_progress >= 1.0:
                self.position = self.current_destination
                self.anim_x, self.anim_y = self.current_destination
                self.is_moving = False
                self.current_destination = None
                self.movement_start_time = None
                self.last_decision_time = time.time()

    def update_movement_decisions(self, current_time):
        """Make decisions about where to move next"""
        if self.is_moving:
            return  # Still moving to current destination
            
        # Check if it's time to make a new movement decision
        time_since_decision = current_time - self.last_decision_time
        should_move = time_since_decision >= self.dwell_time
        
        if should_move and random.random() < self.maneuverability:
            self.choose_next_destination()

    def choose_next_destination(self):
        """Choose next destination based on movement pattern"""
        current_x, current_y = self.position
        
        if self.movement_pattern == "patrol":
            self.patrol_movement()
        elif self.movement_pattern == "circular":
            self.circular_movement()
        elif self.movement_pattern == "evasive":
            self.evasive_movement()
            
    def patrol_movement(self):
        """Move in a patrol pattern within hex grid boundaries"""
        if not self.patrol_points:
            # Generate patrol points within reasonable distance and grid boundaries
            base_x, base_y = self.position
            max_distance = min(self.movement_distance, 4)  # Limit patrol distance
            
            for _ in range(4):
                # Generate random offsets within grid bounds
                attempts = 0
                while attempts < 10:  # Prevent infinite loops
                    offset_x = random.randint(-int(max_distance), int(max_distance))
                    offset_y = random.randint(-int(max_distance), int(max_distance))
                    patrol_x = base_x + offset_x
                    patrol_y = base_y + offset_y
                    
                    # Check if point is within grid boundaries
                    if 0 <= patrol_x < 20 and 0 <= patrol_y < 20:
                        self.patrol_points.append((patrol_x, patrol_y))
                        break
                    attempts += 1
                
            
            # Ensure we have at least one patrol point
            if not self.patrol_points:
                self.patrol_points.append((base_x, base_y))
        
        # Move to next patrol point
        self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
        self.set_destination(self.patrol_points[self.patrol_index])

    def circular_movement(self):
        """Move in a circular pattern within hex grid boundaries"""
        center_x, center_y = self.position
        if not hasattr(self, 'circle_center'):
            self.circle_center = (center_x, center_y)
            self.circle_angle = 0
        
        # Find a suitable radius that keeps us within grid bounds
        max_radius = min(
            self.movement_distance,
            min(self.circle_center[0], 19 - self.circle_center[0]),  # Distance to left/right edges
            min(self.circle_center[1], 19 - self.circle_center[1])   # Distance to top/bottom edges
        )
        max_radius = max(1, int(max_radius))  # Ensure at least radius of 1
        
        self.circle_angle += random.uniform(45, 90)  # 45-90 degree steps
        radius = random.randint(1, max_radius)
        
        dest_x = self.circle_center[0] + radius * math.cos(math.radians(self.circle_angle))
        dest_y = self.circle_center[1] + radius * math.sin(math.radians(self.circle_angle))
        self.set_destination((dest_x, dest_y))

    def evasive_movement(self):
        """Move evasively with random direction changes within hex grid boundaries"""
        current_x, current_y = self.position
        
        # Generate a random hex destination within movement range and grid bounds
        max_distance = min(self.movement_distance, 3)  # Limit evasive distance
        attempts = 0
        
        while attempts < 20:  # Multiple attempts to find valid destination
            angle = random.uniform(0, 360)
            distance = random.randint(1, int(max_distance))
            
            dest_x = current_x + distance * math.cos(math.radians(angle))
            dest_y = current_y + distance * math.sin(math.radians(angle))
            
            # Round to nearest hex center
            dest_x = round(dest_x)
            dest_y = round(dest_y)
            
            # Check if destination is within grid bounds
            if 0 <= dest_x < 20 and 0 <= dest_y < 20:
                self.set_destination((dest_x, dest_y))
                return
            
            attempts += 1
        
        # If no valid destination found, stay put or move to adjacent hex
        adjacent_hexes = [
            (current_x + 1, current_y), (current_x - 1, current_y),
            (current_x, current_y + 1), (current_x, current_y - 1),
            (current_x + 1, current_y - 1), (current_x - 1, current_y + 1)
        ]
        
        # Find valid adjacent hex
        for dest_x, dest_y in adjacent_hexes:
            if 0 <= dest_x < 20 and 0 <= dest_y < 20:
                self.set_destination((dest_x, dest_y))
                return

    def constrain_to_grid(self, q, r, grid_size=20):
        """Constrain coordinates to stay within hex grid boundaries and snap to hex centers"""
        # Clamp to grid boundaries (0 to grid_size-1)
        q_constrained = max(0, min(grid_size - 1, int(round(q))))
        r_constrained = max(0, min(grid_size - 1, int(round(r))))
        return (q_constrained, r_constrained)

    def set_destination(self, destination):
        """Set a new movement destination, constrained to hex grid and avoiding collisions"""
        # Constrain destination to grid boundaries and snap to hex centers
        constrained_dest = self.constrain_to_grid(destination[0], destination[1])
        
        # Check for collisions with other objects (player ship, other enemies, etc.)
        if self.is_destination_blocked(constrained_dest):
            # Try to find an alternative destination nearby
            alternative_dest = self.find_alternative_destination(constrained_dest)
            if alternative_dest:
                constrained_dest = alternative_dest
            else:
                # If no alternative found, don't move
                return
        
        self.current_destination = constrained_dest
        self.is_moving = True
        self.movement_start_time = time.time()
        self.move_progress = 0.0

    def get_render_position(self):
        """Get the current position for rendering (animated position)"""
        return (self.anim_x, self.anim_y)

    def calculate_distance(self, other_position):
        """Calculate distance to another position"""
        return math.sqrt((self.position[0] - other_position[0])**2 + (self.position[1] - other_position[1])**2)

    def fire_at_target(self, target_distance):
        """Legacy method - now uses personality-driven combat system"""
        current_time = time.time()
        self.execute_attack(target_distance, current_time)
    
    def take_damage_from_player(self, damage):
        """Track damage taken from player for adaptation and evasion AI"""
        self.consecutive_hits_taken += 1
        
        # Reset hit counter after some time (adaptation memory)
        def reset_hit_counter():
            time.sleep(5.0)  # 5 second memory
            self.consecutive_hits_taken = max(0, self.consecutive_hits_taken - 1)
        
        import threading
        threading.Thread(target=reset_hit_counter, daemon=True).start()
        
        # Add to player pattern memory for future adaptation
        if len(self.player_pattern_memory) >= 10:
            self.player_pattern_memory.pop(0)  # Keep only recent patterns
        self.player_pattern_memory.append({
            'time': time.time(),
            'damage': damage,
            'distance': self.calculate_distance(self.target.position) if self.target else 0
        })
    
    def get_personality_description(self):
        """Get a description of this enemy's personality for debugging/display"""
        archetype = self.personality['archetype']
        combat_posture = self.combat_posture
        weapon_pref = "Phasers" if self.weapon_preference < 0.5 else "Torpedoes"
        
        return f"{archetype.title()} ({combat_posture}) - Prefers {weapon_pref} at {self.range_preference:.1f} hex range"
    
    def _trigger_weapon_animation(self, weapon_type, distance, damage):
        """Trigger weapon animation through the game's weapon animation manager"""
        # This will be called by the game loop to connect to the weapon animation manager
        # We'll store the weapon firing data for the game loop to pick up
        if not hasattr(self, 'pending_weapon_animations'):
            self.pending_weapon_animations = []
        
        animation_data = {
            'weapon_type': weapon_type,
            'distance': distance,
            'damage': damage,
            'timestamp': time.time()
        }
        self.pending_weapon_animations.append(animation_data)
    
    def get_pending_weapon_animations(self):
        """Get and clear pending weapon animations for processing by game loop"""
        if hasattr(self, 'pending_weapon_animations'):
            animations = self.pending_weapon_animations.copy()
            self.pending_weapon_animations.clear()
            return animations
        return []
    
    def apply_damage(self, raw_damage: int, attacker_ship=None):
        """Override base apply_damage to track damage from player for AI adaptation"""
        # Call parent method to handle actual damage
        super().apply_damage(raw_damage, attacker_ship)
        
        # Track damage from player for personality-driven AI adaptation
        if attacker_ship and hasattr(attacker_ship, 'name') and 'Enterprise' in attacker_ship.name:
            self.take_damage_from_player(raw_damage)
    
    def is_destination_blocked(self, destination):
        """Check if a destination hex is blocked by other objects"""
        dest_x, dest_y = int(destination[0]), int(destination[1])
        
        # Check collision with player ship
        if hasattr(self, 'target') and self.target and hasattr(self.target, 'position'):
            player_x, player_y = int(self.target.position[0]), int(self.target.position[1])
            if dest_x == player_x and dest_y == player_y:
                return True
        
        # Check collision with other objects in the system
        if hasattr(self, 'system_objects') and self.system_objects:
            for obj in self.system_objects:
                if hasattr(obj, 'system_q') and hasattr(obj, 'system_r'):
                    obj_x, obj_y = int(obj.system_q), int(obj.system_r)
                    if dest_x == obj_x and dest_y == obj_y:
                        # Don't collide with ourselves
                        if obj.type == 'enemy' and (obj_x, obj_y) == (int(self.position[0]), int(self.position[1])):
                            continue
                        # Block movement to occupied hexes (but allow planets and some other objects)
                        if obj.type in ['starbase', 'star']:  # Only block major objects
                            return True
                        # Allow movement to same hex as player for close combat
                        # Allow movement to hexes with planets (can orbit)
                        # Only block other enemies if very close to avoid clustering
        
        return False
    
    def find_alternative_destination(self, blocked_destination):
        """Find an alternative destination near the blocked one"""
        dest_x, dest_y = blocked_destination
        
        # Try positions in a circle around the blocked destination
        for radius in range(1, 4):  # Try radius 1, 2, 3
            for angle in range(0, 360, 45):  # Try 8 directions
                offset_x = radius * math.cos(math.radians(angle))
                offset_y = radius * math.sin(math.radians(angle))
                
                alt_x = dest_x + offset_x
                alt_y = dest_y + offset_y
                
                # Constrain to grid
                alt_dest = self.constrain_to_grid(alt_x, alt_y)
                
                # Check if this alternative is not blocked
                if not self.is_destination_blocked(alt_dest):
                    return alt_dest
        
        return None  # No alternative found

    def pursue_target(self):
        """Move towards target when in pursuit range"""
        if not self.is_moving:
            current_x, current_y = self.position
            target_x, target_y = self.target.position
            
            dx = target_x - current_x
            dy = target_y - current_y
            
            # Calculate direction but move to hex centers
            if abs(dx) > abs(dy):
                # Move horizontally toward target
                dest_x = current_x + (1 if dx > 0 else -1)
                dest_y = current_y
            else:
                # Move vertically toward target
                dest_x = current_x
                dest_y = current_y + (1 if dy > 0 else -1)
            
            # Ensure destination is within grid bounds
            dest_x = max(0, min(19, dest_x))
            dest_y = max(0, min(19, dest_y))
            
            self.set_destination((dest_x, dest_y)) 