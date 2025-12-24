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
        self.decision_cooldown = 500   # 0.5 seconds between major decisions
        
        # Retaliation state
        self.under_attack = False
        self.last_attacked_time = 0
        self.retaliation_mode_duration = 10000  # 10 seconds of aggressive retaliation
        
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
            # Trigger immediate retaliation mode
            self._trigger_retaliation_mode()
    
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
            # Trigger immediate retaliation mode
            self._trigger_retaliation_mode()
    
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

    def _trigger_retaliation_mode(self):
        """Trigger immediate aggressive retaliation when ship takes damage"""
        import time
        current_time = time.time() * 1000
        
        self.under_attack = True
        self.last_attacked_time = current_time
        self.ai_state = "attack"  # Immediately switch to attack mode
        
        # Reset decision cooldown for immediate response
        self.last_decision_time = 0
        
        print(f"[KLINGON] {self.name} under attack! Engaging with extreme prejudice!")

    def update_ai(self, delta_time):
        """Main AI update loop - makes decisions and executes actions"""
        if not self.target:
            return
            
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Check if still in retaliation mode
        if self.under_attack:
            time_since_attacked = current_time - self.last_attacked_time
            if time_since_attacked > self.retaliation_mode_duration:
                self.under_attack = False
                print(f"[KLINGON] {self.name} retaliation mode expired, returning to normal tactics")
        
        # Update movement animation if moving
        self._update_movement_animation(current_time)
        
        # Update weapon cooldowns
        self._update_weapon_cooldowns(current_time)
        
        # Make tactical decisions based on personality and situation
        # In retaliation mode, react much faster
        if self.under_attack:
            decision_interval = 100  # 0.1 seconds - immediate decisions when retaliating
        else:
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
        """Move closer to the target using hex-based navigation"""
        if not self.target or self.is_moving:
            return
            
        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return
        
        # Get current and target hex coordinates
        current_hex = (int(self.position[0]), int(self.position[1]))
        target_hex = (int(target_pos[0]), int(target_pos[1]))
        
        # Calculate direction to target in hex space
        dx = target_hex[0] - current_hex[0]
        dy = target_hex[1] - current_hex[1]
        
        if dx == 0 and dy == 0:
            return  # Already at target hex
        
        # Determine movement distance (1-3 hexes based on personality)
        max_move_distance = int(self.personality['move_distance'])
        move_distance = random.randint(1, max_move_distance)
        
        # Calculate unit direction vector
        distance_to_target = math.sqrt(dx * dx + dy * dy)
        if distance_to_target > 0:
            unit_dx = dx / distance_to_target
            unit_dy = dy / distance_to_target
            
            # Calculate new hex position
            new_hex_x = current_hex[0] + int(unit_dx * move_distance)
            new_hex_y = current_hex[1] + int(unit_dy * move_distance)
            
            # Add some personality-based variation (occasionally move to adjacent hex)
            if random.random() < self.personality['unpredictability']:
                new_hex_x += random.randint(-1, 1)
                new_hex_y += random.randint(-1, 1)
            
            self._start_movement((new_hex_x, new_hex_y))
    
    def _move_away_from_target(self):
        """Move away from the target using hex-based navigation"""
        if not self.target or self.is_moving:
            return
            
        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return
        
        # Get current and target hex coordinates
        current_hex = (int(self.position[0]), int(self.position[1]))
        target_hex = (int(target_pos[0]), int(target_pos[1]))
        
        # Calculate direction away from target in hex space
        dx = current_hex[0] - target_hex[0]  # Reverse direction
        dy = current_hex[1] - target_hex[1]
        
        # Determine movement distance (1-3 hexes based on personality)
        max_move_distance = int(self.personality['move_distance'])
        move_distance = random.randint(1, max_move_distance)
        
        # If already far enough, don't move further away
        distance_to_target = math.sqrt(dx * dx + dy * dy)
        if distance_to_target == 0:
            # Same hex as target, pick random direction
            dx, dy = random.choice([(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1), (1,-1), (-1,1)])
        else:
            # Normalize direction
            dx = dx / distance_to_target
            dy = dy / distance_to_target
        
        # Calculate new hex position
        new_hex_x = current_hex[0] + int(dx * move_distance)
        new_hex_y = current_hex[1] + int(dy * move_distance)
        
        # Add evasion patterns based on skill
        if random.random() < self.personality['evasion_skill']:
            new_hex_x += random.randint(-1, 1)
            new_hex_y += random.randint(-1, 1)
        
        self._start_movement((new_hex_x, new_hex_y))
    
    def _move_to_flank_position(self):
        """Move to a flanking position relative to target using hex-based navigation"""
        if not self.target or self.is_moving:
            return
            
        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return
        
        # Get current and target hex coordinates
        current_hex = (int(self.position[0]), int(self.position[1]))
        target_hex = (int(target_pos[0]), int(target_pos[1]))
        
        # Calculate perpendicular directions for flanking
        dx = target_hex[0] - current_hex[0]
        dy = target_hex[1] - current_hex[1]
        
        # Choose a perpendicular direction (rotate 90 degrees)
        if random.random() < 0.5:
            flank_dx, flank_dy = -dy, dx  # Rotate left
        else:
            flank_dx, flank_dy = dy, -dx  # Rotate right
        
        # Normalize and scale by desired flanking distance
        flank_distance = int(self.preferred_range * 0.8)
        if flank_distance == 0:
            flank_distance = 2
        
        # Calculate flanking hex position
        if flank_dx != 0 or flank_dy != 0:
            flank_length = math.sqrt(flank_dx * flank_dx + flank_dy * flank_dy)
            flank_dx = int((flank_dx / flank_length) * flank_distance)
            flank_dy = int((flank_dy / flank_length) * flank_distance)
        
        new_hex_x = target_hex[0] + flank_dx
        new_hex_y = target_hex[1] + flank_dy
        
        self._start_movement((new_hex_x, new_hex_y))
    
    def _move_randomly(self):
        """Random patrol movement using hex-based navigation"""
        if self.is_moving:
            return
        
        # Get current hex coordinates
        current_hex = (int(self.position[0]), int(self.position[1]))
        
        # Choose random direction (8 directions + stay put)
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),  # Cardinal directions
            (1, 1), (-1, -1), (1, -1), (-1, 1),  # Diagonal directions
            (0, 0)  # Stay put (low chance)
        ]
        
        direction = random.choice(directions)
        
        # Determine movement distance (1-3 hexes based on personality)
        max_move_distance = int(self.personality['move_distance'])
        move_distance = random.randint(1, max_move_distance)
        
        # Calculate new hex position
        new_hex_x = current_hex[0] + (direction[0] * move_distance)
        new_hex_y = current_hex[1] + (direction[1] * move_distance)
        
        self._start_movement((new_hex_x, new_hex_y))
    
    def _start_movement(self, target_position):
        """Begin movement animation to target position"""
        # Enforce hex grid boundaries
        constrained_position = self._constrain_to_grid(target_position)
        self.target_position = constrained_position
        self.is_moving = True
        self.movement_start_time = time.time() * 1000
        self.movement_duration = 2000 / self.personality['movement_speed']  # Adjusted by speed
    
    def _constrain_to_grid(self, position):
        """Constrain position to stay within hex grid boundaries and ensure integer hex coordinates"""
        x, y = position
        # Ensure coordinates are integers for hex-based navigation
        hex_x = int(round(x))
        hex_y = int(round(y))
        
        # Grid boundaries from constants.py: 20x20 hex grid (0-19 for both x and y)
        constrained_x = max(0, min(hex_x, constants.GRID_COLS - 1))
        constrained_y = max(0, min(hex_y, constants.GRID_ROWS - 1))
        
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