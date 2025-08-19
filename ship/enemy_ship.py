import random
import math
import time
from .base_ship import BaseShip
from data import constants
from ship.ship_systems.shield import Shield


class EnemyShip(BaseShip):
    """Dynamic Klingon warship with intelligent AI and randomized personality"""
    
    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy, weapons=None, position=None):
        enemy_shield = Shield(max_shield_strength, self)
        super().__init__(name, enemy_shield, hull_strength, energy, max_energy, weapons, position)
        
        # Position and movement state
        self.position = position if position else (0, 0)
        self.target_position = None
        self.is_moving = False
        self.current_destination = None
        self.movement_progress = 0.0
        self.movement_start_time = 0
        self.movement_duration = 2000  # Base movement time in ms
        
        # Combat compatibility properties
        self._shields = max_shield_strength
        self._max_shields = max_shield_strength
        self._health = hull_strength
        
        # AI State Management
        self.target = None
        self.system_objects = []
        self.ai_state = "patrol"  # patrol, pursue, attack, retreat, flank
        self.last_player_position = None
        self.damage_taken_this_turn = 0
        self.total_damage_taken = 0
        self.turns_since_last_attack = 0
        self.turns_in_current_state = 0
        
        # Generate Randomized Personality Parameters
        self.personality = self._generate_personality()
        
        # Weapon state
        self.weapon_cooldown = 0
        self.last_weapon_fire_time = 0
        self.pending_weapon_animations = []
        
        # Tactical state
        self.preferred_range = self.personality['attack_range']
        self.last_decision_time = 0
        self.decision_cooldown = 1000  # 1 second between major decisions
        
        print(f"[KLINGON] {name} warship created with personality: "
              f"Aggression={self.personality['aggression']:.2f}, "
              f"Courage={self.personality['courage']:.2f}, "
              f"Speed={self.personality['movement_speed']:.2f}")
    
    def _generate_personality(self):
        """Generate randomized personality parameters for this Klingon warrior"""
        return {
            # Movement traits
            'movement_speed': random.uniform(constants.KLINGON_MOVEMENT_SPEED_MIN, constants.KLINGON_MOVEMENT_SPEED_MAX),
            'move_distance': random.uniform(constants.KLINGON_MOVE_DISTANCE_MIN, constants.KLINGON_MOVE_DISTANCE_MAX),
            'move_variability': random.uniform(constants.KLINGON_MOVE_VARIABILITY_MIN, constants.KLINGON_MOVE_VARIABILITY_MAX),
            
            # Combat traits
            'aggression': random.uniform(constants.KLINGON_AGGRESSION_MIN, constants.KLINGON_AGGRESSION_MAX),
            'attack_range': random.uniform(constants.KLINGON_ATTACK_RANGE_MIN, constants.KLINGON_ATTACK_RANGE_MAX),
            'closing_tendency': random.uniform(constants.KLINGON_CLOSING_TENDENCY_MIN, constants.KLINGON_CLOSING_TENDENCY_MAX),
            
            # Weapon traits
            'weapon_power': random.uniform(constants.KLINGON_WEAPON_POWER_MIN, constants.KLINGON_WEAPON_POWER_MAX),
            'firing_frequency': random.uniform(constants.KLINGON_FIRING_FREQUENCY_MIN, constants.KLINGON_FIRING_FREQUENCY_MAX),
            'weapon_accuracy': random.uniform(constants.KLINGON_WEAPON_ACCURACY_MIN, constants.KLINGON_WEAPON_ACCURACY_MAX),
            
            # Tactical traits
            'flanking_tendency': random.uniform(constants.KLINGON_FLANKING_TENDENCY_MIN, constants.KLINGON_FLANKING_TENDENCY_MAX),
            'evasion_skill': random.uniform(constants.KLINGON_EVASION_SKILL_MIN, constants.KLINGON_EVASION_SKILL_MAX),
            'tactical_patience': random.uniform(constants.KLINGON_TACTICAL_PATIENCE_MIN, constants.KLINGON_TACTICAL_PATIENCE_MAX),
            
            # Defensive traits
            'retreat_threshold': random.uniform(constants.KLINGON_RETREAT_THRESHOLD_MIN, constants.KLINGON_RETREAT_THRESHOLD_MAX),
            'shield_priority': random.uniform(constants.KLINGON_SHIELD_PRIORITY_MIN, constants.KLINGON_SHIELD_PRIORITY_MAX),
            'damage_avoidance': random.uniform(constants.KLINGON_DAMAGE_AVOIDANCE_MIN, constants.KLINGON_DAMAGE_AVOIDANCE_MAX),
            
            # Personality traits
            'courage': random.uniform(constants.KLINGON_COURAGE_MIN, constants.KLINGON_COURAGE_MAX),
            'unpredictability': random.uniform(constants.KLINGON_UNPREDICTABILITY_MIN, constants.KLINGON_UNPREDICTABILITY_MAX),
            'honor_code': random.uniform(constants.KLINGON_HONOR_CODE_MIN, constants.KLINGON_HONOR_CODE_MAX),
            'vengeance_factor': random.uniform(constants.KLINGON_VENGEANCE_FACTOR_MIN, constants.KLINGON_VENGEANCE_FACTOR_MAX),
            
            # Advanced traits
            'power_management': random.uniform(constants.KLINGON_POWER_MANAGEMENT_MIN, constants.KLINGON_POWER_MANAGEMENT_MAX),
            'reaction_time': random.uniform(constants.KLINGON_REACTION_TIME_MIN, constants.KLINGON_REACTION_TIME_MAX),
            'pursuit_persistence': random.uniform(constants.KLINGON_PURSUIT_PERSISTENCE_MIN, constants.KLINGON_PURSUIT_PERSISTENCE_MAX),
        }
    
    @property
    def shields(self):
        """Shield strength for combat system compatibility"""
        return self._shields
    
    @shields.setter
    def shields(self, value):
        """Set shield strength for combat system compatibility"""
        old_shields = self._shields
        self._shields = max(0, value)
        # Track damage taken for AI reactions
        if old_shields > self._shields:
            damage = old_shields - self._shields
            self.damage_taken_this_turn += damage
            self.total_damage_taken += damage
    
    @property
    def health(self):
        """Hull health for combat system compatibility"""
        return self._health
    
    @health.setter
    def health(self, value):
        """Set hull health for combat system compatibility"""
        old_health = self._health
        self._health = max(0, value)
        # Track damage taken for AI reactions
        if old_health > self._health:
            damage = old_health - self._health
            self.damage_taken_this_turn += damage
            self.total_damage_taken += damage
    
    @property
    def max_shields(self):
        """Maximum shield strength for combat system compatibility"""
        return self._max_shields
    
    def get_health_percentage(self):
        """Get current health as percentage of maximum"""
        max_health = self.max_hull_strength
        return self._health / max_health if max_health > 0 else 0
    
    def get_shield_percentage(self):
        """Get current shields as percentage of maximum"""
        return self._shields / self._max_shields if self._max_shields > 0 else 0
        
    def set_target(self, target):
        """Set the player ship as our target"""
        self.target = target
        if target:
            self.last_player_position = getattr(target, 'position', None)
    
    def set_system_objects(self, system_objects):
        """Set all objects in the current system for tactical awareness"""
        self.system_objects = system_objects if system_objects else []

    def update_ai(self, delta_time):
        """Main AI update loop - makes decisions and executes actions"""
        if not self.target:
            return
            
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Update movement animation if moving
        self._update_movement_animation(current_time)
        
        # Update weapon cooldowns
        self._update_weapon_cooldowns(current_time)
        
        # Make tactical decisions based on personality and situation
        decision_interval = self.decision_cooldown / self.personality['reaction_time']
        time_since_last_decision = current_time - self.last_decision_time
        
        if time_since_last_decision > decision_interval:
            self._make_tactical_decision(current_time)
            self.last_decision_time = current_time
        
        # Execute current AI state
        self._execute_ai_state(current_time)
        
        # Reset per-turn damage tracking
        self.damage_taken_this_turn = 0
        self.turns_in_current_state += 1
    
    def _update_movement_animation(self, current_time):
        """Update position if currently moving"""
        if not self.is_moving or not self.target_position:
            return
            
        elapsed = current_time - self.movement_start_time
        progress = min(elapsed / self.movement_duration, 1.0)
        
        if progress >= 1.0:
            # Movement complete
            self.position = self.target_position
            self.is_moving = False
            self.target_position = None
            self.current_destination = None
        else:
            # Interpolate position
            start_x, start_y = self.position
            target_x, target_y = self.target_position
            current_x = start_x + (target_x - start_x) * progress
            current_y = start_y + (target_y - start_y) * progress
            self.current_destination = (current_x, current_y)
    
    def _update_weapon_cooldowns(self, current_time):
        """Update weapon system cooldowns"""
        if self.weapon_cooldown > 0:
            time_since_last_shot = current_time - self.last_weapon_fire_time
            self.weapon_cooldown = max(0, self.weapon_cooldown - time_since_last_shot)
    
    def _make_tactical_decision(self, current_time):
        """Make high-level tactical decisions based on situation and personality"""
        if not self.target:
            self.ai_state = "patrol"
            return
            
        # Calculate situation factors
        distance_to_player = self._get_distance_to_target()
        health_percentage = self.get_health_percentage()
        shield_percentage = self.get_shield_percentage()
        
        # Determine if we should retreat
        if health_percentage < self.personality['retreat_threshold']:
            if self.personality['courage'] < 0.5 or random.random() < (1.0 - self.personality['courage']):
                self.ai_state = "retreat"
                return
        
        # Determine combat state based on distance and aggression
        if distance_to_player <= self.preferred_range * 1.5:
            # Close enough to engage
            if self.personality['aggression'] > 0.6:
                self.ai_state = "attack"
            elif random.random() < self.personality['flanking_tendency']:
                self.ai_state = "flank"
            else:
                self.ai_state = "pursue"
        else:
            # Too far away, need to close distance
            if self.personality['closing_tendency'] > 0.5:
                self.ai_state = "pursue"
            else:
                self.ai_state = "patrol"
    
    def _execute_ai_state(self, current_time):
        """Execute actions based on current AI state"""
        if self.ai_state == "attack":
            self._execute_attack_behavior(current_time)
        elif self.ai_state == "pursue":
            self._execute_pursue_behavior(current_time)
        elif self.ai_state == "retreat":
            self._execute_retreat_behavior(current_time)
        elif self.ai_state == "flank":
            self._execute_flank_behavior(current_time)
        else:  # patrol
            self._execute_patrol_behavior(current_time)
    
    def _execute_attack_behavior(self, current_time):
        """Aggressive attack behavior"""
        # Try to fire weapons
        if self._should_fire_weapon() and self.weapon_cooldown <= 0:
            self._fire_weapon(current_time)
        
        # Move to optimal attack range
        distance = self._get_distance_to_target()
        if distance > self.preferred_range:
            self._move_toward_target()
        elif distance < self.preferred_range * 0.7:
            # Too close, back off slightly
            self._move_away_from_target()
    
    def _execute_pursue_behavior(self, current_time):
        """Chase the player to get into attack range"""
        distance = self._get_distance_to_target()
        if distance > self.preferred_range:
            self._move_toward_target()
        else:
            # In range, switch to attack
            self.ai_state = "attack"
    
    def _execute_retreat_behavior(self, current_time):
        """Defensive retreat behavior"""
        self._move_away_from_target()
        
        # Occasionally fire while retreating if brave enough
        if (self.personality['courage'] > 0.3 and 
            random.random() < self.personality['firing_frequency'] * 0.5 and
            self.weapon_cooldown <= 0):
            self._fire_weapon(current_time)
    
    def _execute_flank_behavior(self, current_time):
        """Attempt flanking maneuvers"""
        # Move to a flanking position (perpendicular to player)
        self._move_to_flank_position()
        
        # Fire if in good position
        if self._should_fire_weapon() and self.weapon_cooldown <= 0:
            self._fire_weapon(current_time)
    
    def _execute_patrol_behavior(self, current_time):
        """Random patrol movement"""
        self._move_randomly()
    
    def _get_distance_to_target(self):
        """Calculate distance to the target player"""
        if not self.target or not hasattr(self.target, 'position'):
            return float('inf')
        
        px, py = self.target.position
        ex, ey = self.position
        return math.hypot(px - ex, py - ey)
    
    def _should_fire_weapon(self):
        """Determine if we should fire a weapon this turn"""
        # Use personality-based firing frequency with proper balance
        # Since this is called ~60 times per second, convert personality trait to per-frame chance
        base_firing_chance = self.personality['firing_frequency']  # 0.05 to 0.15 typically
        firing_chance_per_frame = base_firing_chance * 0.005  # Convert to reasonable per-frame rate
        
        should_fire = random.random() < firing_chance_per_frame
        
        
        return should_fire
    
    def _fire_weapon(self, current_time):
        """Fire disruptors at the target"""
        if not self.target:
            return
            
            
        
        # Create weapon animation for disruptor fire
        weapon_animation = {
            'type': 'disruptor',
            'start_time': current_time,
            'target': self.target,
            'accuracy': self.personality['weapon_accuracy'],
            'power': self.personality['weapon_power']
        }
        
        self.pending_weapon_animations.append(weapon_animation)
        self.weapon_cooldown = constants.ENEMY_WEAPON_COOLDOWN_SECONDS * 1000  # Convert seconds to milliseconds
        self.last_weapon_fire_time = current_time
    
    def _move_toward_target(self):
        """Move closer to the target"""
        if not self.target or self.is_moving:
            return
            
        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return
        
        # Calculate direction to target
        tx, ty = target_pos
        ex, ey = self.position
        
        # Add some personality-based variation
        angle_variance = self.personality['unpredictability'] * 0.5  # Up to 30 degrees
        angle = math.atan2(ty - ey, tx - ex) + random.uniform(-angle_variance, angle_variance)
        
        # Calculate new position
        distance = self.personality['move_distance'] * (1 + random.uniform(-self.personality['move_variability'], self.personality['move_variability']))
        new_x = ex + math.cos(angle) * distance
        new_y = ey + math.sin(angle) * distance
        
        self._start_movement((new_x, new_y))
    
    def _move_away_from_target(self):
        """Move away from the target"""
        if not self.target or self.is_moving:
            return
            
        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return
        
        # Calculate direction away from target
        tx, ty = target_pos
        ex, ey = self.position
        
        angle = math.atan2(ey - ty, ex - tx)  # Reverse direction
        
        # Add evasion patterns based on skill
        if random.random() < self.personality['evasion_skill']:
            angle += random.uniform(-0.7, 0.7)  # Evasive maneuvering
        
        distance = self.personality['move_distance']
        new_x = ex + math.cos(angle) * distance
        new_y = ey + math.sin(angle) * distance
        
        self._start_movement((new_x, new_y))
    
    def _move_to_flank_position(self):
        """Move to a flanking position relative to target"""
        if not self.target or self.is_moving:
            return
            
        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return
        
        tx, ty = target_pos
        ex, ey = self.position
        
        # Calculate perpendicular angle for flanking
        to_target_angle = math.atan2(ty - ey, tx - ex)
        flank_angle = to_target_angle + (math.pi / 2 if random.random() < 0.5 else -math.pi / 2)
        
        distance = self.preferred_range * 0.8
        new_x = tx + math.cos(flank_angle) * distance
        new_y = ty + math.sin(flank_angle) * distance
        
        self._start_movement((new_x, new_y))
    
    def _move_randomly(self):
        """Random patrol movement"""
        if self.is_moving:
            return
            
        angle = random.uniform(0, 2 * math.pi)
        distance = self.personality['move_distance'] * random.uniform(0.5, 1.5)
        
        ex, ey = self.position
        new_x = ex + math.cos(angle) * distance
        new_y = ey + math.sin(angle) * distance
        self._start_movement((new_x, new_y))
    
    def _start_movement(self, target_position):
        """Begin movement animation to target position"""
        # Enforce hex grid boundaries
        constrained_position = self._constrain_to_grid(target_position)
        self.target_position = constrained_position
        self.is_moving = True
        self.movement_start_time = time.time() * 1000
        self.movement_duration = 2000 / self.personality['movement_speed']  # Adjusted by speed
    
    def _constrain_to_grid(self, position):
        """Constrain position to stay within hex grid boundaries"""
        x, y = position
        # Grid boundaries from constants.py: 20x20 hex grid (0-19 for both x and y)
        constrained_x = max(0, min(x, constants.GRID_COLS - 1))
        constrained_y = max(0, min(y, constants.GRID_ROWS - 1))
        
        
        return (constrained_x, constrained_y)
    
    def get_render_position(self):
        """Get current position for rendering (includes animation)"""
        if self.is_moving and self.current_destination:
            return self.current_destination
        return self.position
    
    def get_pending_weapon_animations(self):
        """Return list of weapon animations for the combat system"""
        animations = self.pending_weapon_animations.copy()
        self.pending_weapon_animations.clear()  # Clear after returning
        return animations