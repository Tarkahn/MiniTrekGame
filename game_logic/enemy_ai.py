"""
Enemy AI System for Klingon warships.

This module contains the AI behavior logic separated from the EnemyShip class,
allowing for easier testing, modification, and potential reuse for different
enemy types.
"""

import random
import math
import time
from data import constants


class EnemyPersonality:
    """Generates and stores randomized personality parameters for an enemy ship."""

    def __init__(self):
        """Generate randomized personality parameters for this Klingon warrior."""
        # Movement traits
        self.movement_speed = random.uniform(
            constants.KLINGON_MOVEMENT_SPEED_MIN,
            constants.KLINGON_MOVEMENT_SPEED_MAX
        )
        self.move_distance = random.uniform(
            constants.KLINGON_MOVE_DISTANCE_MIN,
            constants.KLINGON_MOVE_DISTANCE_MAX
        )
        self.move_variability = random.uniform(
            constants.KLINGON_MOVE_VARIABILITY_MIN,
            constants.KLINGON_MOVE_VARIABILITY_MAX
        )

        # Combat traits
        self.aggression = random.uniform(
            constants.KLINGON_AGGRESSION_MIN,
            constants.KLINGON_AGGRESSION_MAX
        )
        self.attack_range = random.uniform(
            constants.KLINGON_ATTACK_RANGE_MIN,
            constants.KLINGON_ATTACK_RANGE_MAX
        )
        self.closing_tendency = random.uniform(
            constants.KLINGON_CLOSING_TENDENCY_MIN,
            constants.KLINGON_CLOSING_TENDENCY_MAX
        )

        # Weapon traits
        self.weapon_power = random.uniform(
            constants.KLINGON_WEAPON_POWER_MIN,
            constants.KLINGON_WEAPON_POWER_MAX
        )
        self.firing_frequency = random.uniform(
            constants.KLINGON_FIRING_FREQUENCY_MIN,
            constants.KLINGON_FIRING_FREQUENCY_MAX
        )
        self.weapon_accuracy = random.uniform(
            constants.KLINGON_WEAPON_ACCURACY_MIN,
            constants.KLINGON_WEAPON_ACCURACY_MAX
        )

        # Tactical traits
        self.flanking_tendency = random.uniform(
            constants.KLINGON_FLANKING_TENDENCY_MIN,
            constants.KLINGON_FLANKING_TENDENCY_MAX
        )
        self.evasion_skill = random.uniform(
            constants.KLINGON_EVASION_SKILL_MIN,
            constants.KLINGON_EVASION_SKILL_MAX
        )
        self.tactical_patience = random.uniform(
            constants.KLINGON_TACTICAL_PATIENCE_MIN,
            constants.KLINGON_TACTICAL_PATIENCE_MAX
        )

        # Defensive traits
        self.retreat_threshold = random.uniform(
            constants.KLINGON_RETREAT_THRESHOLD_MIN,
            constants.KLINGON_RETREAT_THRESHOLD_MAX
        )
        self.shield_priority = random.uniform(
            constants.KLINGON_SHIELD_PRIORITY_MIN,
            constants.KLINGON_SHIELD_PRIORITY_MAX
        )
        self.damage_avoidance = random.uniform(
            constants.KLINGON_DAMAGE_AVOIDANCE_MIN,
            constants.KLINGON_DAMAGE_AVOIDANCE_MAX
        )

        # Personality traits
        self.courage = random.uniform(
            constants.KLINGON_COURAGE_MIN,
            constants.KLINGON_COURAGE_MAX
        )
        self.unpredictability = random.uniform(
            constants.KLINGON_UNPREDICTABILITY_MIN,
            constants.KLINGON_UNPREDICTABILITY_MAX
        )
        self.honor_code = random.uniform(
            constants.KLINGON_HONOR_CODE_MIN,
            constants.KLINGON_HONOR_CODE_MAX
        )
        self.vengeance_factor = random.uniform(
            constants.KLINGON_VENGEANCE_FACTOR_MIN,
            constants.KLINGON_VENGEANCE_FACTOR_MAX
        )

        # Advanced traits
        self.power_management = random.uniform(
            constants.KLINGON_POWER_MANAGEMENT_MIN,
            constants.KLINGON_POWER_MANAGEMENT_MAX
        )
        self.reaction_time = random.uniform(
            constants.KLINGON_REACTION_TIME_MIN,
            constants.KLINGON_REACTION_TIME_MAX
        )
        self.pursuit_persistence = random.uniform(
            constants.KLINGON_PURSUIT_PERSISTENCE_MIN,
            constants.KLINGON_PURSUIT_PERSISTENCE_MAX
        )

    def to_dict(self):
        """Convert personality to dictionary format for backwards compatibility."""
        return {
            'movement_speed': self.movement_speed,
            'move_distance': self.move_distance,
            'move_variability': self.move_variability,
            'aggression': self.aggression,
            'attack_range': self.attack_range,
            'closing_tendency': self.closing_tendency,
            'weapon_power': self.weapon_power,
            'firing_frequency': self.firing_frequency,
            'weapon_accuracy': self.weapon_accuracy,
            'flanking_tendency': self.flanking_tendency,
            'evasion_skill': self.evasion_skill,
            'tactical_patience': self.tactical_patience,
            'retreat_threshold': self.retreat_threshold,
            'shield_priority': self.shield_priority,
            'damage_avoidance': self.damage_avoidance,
            'courage': self.courage,
            'unpredictability': self.unpredictability,
            'honor_code': self.honor_code,
            'vengeance_factor': self.vengeance_factor,
            'power_management': self.power_management,
            'reaction_time': self.reaction_time,
            'pursuit_persistence': self.pursuit_persistence,
        }

    def __getitem__(self, key):
        """Allow dictionary-style access for backwards compatibility."""
        return getattr(self, key)


class EnemyAI:
    """
    AI controller for enemy ships.

    Handles tactical decisions, movement behaviors, and combat logic
    separately from the ship's physical properties.
    """

    # AI States
    STATE_PATROL = "patrol"
    STATE_PURSUE = "pursue"
    STATE_ATTACK = "attack"
    STATE_RETREAT = "retreat"
    STATE_FLANK = "flank"
    STATE_REPAIR = "repair"

    def __init__(self, ship, personality=None):
        """
        Initialize the AI controller.

        Args:
            ship: The EnemyShip instance this AI controls
            personality: Optional EnemyPersonality instance (generates new if None)
        """
        self.ship = ship
        self.personality = personality if personality else EnemyPersonality()

        # Target tracking
        self.target = None
        self.system_objects = []
        self.last_player_position = None

        # AI state
        self.state = self.STATE_PATROL
        self.turns_in_current_state = 0
        self.damage_taken_this_turn = 0
        self.total_damage_taken = 0

        # Decision timing
        self.last_decision_time = 0
        self.decision_cooldown = 500  # 0.5 seconds between major decisions

        # Retaliation state
        self.under_attack = False
        self.last_attacked_time = 0
        self.retaliation_mode_duration = 10000  # 10 seconds

        # Preferred combat range
        self.preferred_range = self.personality.attack_range

    def set_target(self, target):
        """Set the player ship as the target."""
        self.target = target
        if target:
            self.last_player_position = getattr(target, 'position', None)

    def set_system_objects(self, system_objects):
        """Set all objects in the current system for tactical awareness."""
        self.system_objects = system_objects if system_objects else []

    def trigger_retaliation_mode(self):
        """Trigger immediate aggressive retaliation when ship takes damage."""
        current_time = time.time() * 1000

        self.under_attack = True
        self.last_attacked_time = current_time
        self.state = self.STATE_ATTACK

        # Reset decision cooldown for immediate response
        self.last_decision_time = 0

        print(f"[KLINGON] {self.ship.name} under attack! Engaging with extreme prejudice!")

    def record_damage(self, amount):
        """Record damage taken for AI reactions."""
        self.damage_taken_this_turn += amount
        self.total_damage_taken += amount
        self.trigger_retaliation_mode()

    def update(self, delta_time):
        """
        Main AI update loop - makes decisions and executes actions.

        Args:
            delta_time: Time since last update in seconds
        """
        if not self.target:
            return

        current_time = time.time() * 1000

        # Check if still in retaliation mode
        if self.under_attack:
            time_since_attacked = current_time - self.last_attacked_time
            if time_since_attacked > self.retaliation_mode_duration:
                self.under_attack = False
                print(f"[KLINGON] {self.ship.name} retaliation mode expired")

        # Make tactical decisions based on personality and situation
        if self.under_attack:
            decision_interval = 100  # Immediate decisions when retaliating
        else:
            decision_interval = self.decision_cooldown / self.personality.reaction_time

        time_since_last_decision = current_time - self.last_decision_time

        if time_since_last_decision > decision_interval:
            self._make_tactical_decision(current_time)
            self.last_decision_time = current_time

        # Execute current AI state
        self._execute_state(current_time)

        # Reset per-turn damage tracking
        self.damage_taken_this_turn = 0
        self.turns_in_current_state += 1

    def _make_tactical_decision(self, current_time):
        """Make high-level tactical decisions based on situation and personality."""
        if not self.target:
            # No target - check if we should repair while idle
            if self._should_repair():
                self.state = self.STATE_REPAIR
            else:
                self.state = self.STATE_PATROL
            return

        # Calculate situation factors
        distance_to_player = self._get_distance_to_target()
        health_percentage = self.ship.get_health_percentage()

        # Determine if we should retreat
        if health_percentage < self.personality.retreat_threshold:
            if (self.personality.courage < 0.5 or
                    random.random() < (1.0 - self.personality.courage)):
                self.state = self.STATE_RETREAT
                return

        # Check if we should repair (only when not under direct attack and at safe distance)
        if self._should_repair() and not self.under_attack and distance_to_player > self.preferred_range * 2:
            self.state = self.STATE_REPAIR
            return

        # Determine combat state based on distance and aggression
        if distance_to_player <= self.preferred_range * 1.5:
            # Close enough to engage
            if self.personality.aggression > 0.6:
                self.state = self.STATE_ATTACK
            elif random.random() < self.personality.flanking_tendency:
                self.state = self.STATE_FLANK
            else:
                self.state = self.STATE_PURSUE
        else:
            # Too far away, need to close distance
            if self.personality.closing_tendency > 0.5:
                self.state = self.STATE_PURSUE
            else:
                self.state = self.STATE_PATROL

    def _execute_state(self, current_time):
        """Execute actions based on current AI state."""
        if self.state == self.STATE_ATTACK:
            self._execute_attack(current_time)
        elif self.state == self.STATE_PURSUE:
            self._execute_pursue(current_time)
        elif self.state == self.STATE_RETREAT:
            self._execute_retreat(current_time)
        elif self.state == self.STATE_FLANK:
            self._execute_flank(current_time)
        elif self.state == self.STATE_REPAIR:
            self._execute_repair(current_time)
        else:
            self._execute_patrol(current_time)

    def _execute_attack(self, current_time):
        """Aggressive attack behavior."""
        # Try to fire weapons
        if self.should_fire_weapon() and self.ship.weapon_cooldown <= 0:
            self._fire_weapon(current_time)

        # Move to optimal attack range
        distance = self._get_distance_to_target()
        if distance > self.preferred_range:
            self.move_toward_target()
        elif distance < self.preferred_range * 0.7:
            self.move_away_from_target()

    def _execute_pursue(self, current_time):
        """Chase the player to get into attack range."""
        distance = self._get_distance_to_target()
        if distance > self.preferred_range:
            self.move_toward_target()
        else:
            self.state = self.STATE_ATTACK

    def _execute_retreat(self, current_time):
        """Defensive retreat behavior."""
        self.move_away_from_target()

        # Occasionally fire while retreating if brave enough
        if (self.personality.courage > 0.3 and
                random.random() < self.personality.firing_frequency * 0.5 and
                self.ship.weapon_cooldown <= 0):
            self._fire_weapon(current_time)

    def _execute_flank(self, current_time):
        """Attempt flanking maneuvers."""
        self.move_to_flank_position()

        if self.should_fire_weapon() and self.ship.weapon_cooldown <= 0:
            self._fire_weapon(current_time)

    def _execute_patrol(self, current_time):
        """Random patrol movement."""
        self.move_randomly()

    def _get_distance_to_target(self):
        """Calculate distance to the target player."""
        if not self.target or not hasattr(self.target, 'position'):
            return float('inf')

        px, py = self.target.position
        ex, ey = self.ship.position
        return math.hypot(px - ex, py - ey)

    def should_fire_weapon(self):
        """Determine if we should fire a weapon this turn."""
        base_firing_chance = self.personality.firing_frequency
        firing_chance_per_frame = base_firing_chance * 0.005
        return random.random() < firing_chance_per_frame

    def _fire_weapon(self, current_time):
        """Fire disruptors at the target."""
        if not self.target:
            return

        weapon_animation = {
            'type': 'disruptor',
            'start_time': current_time,
            'target': self.target,
            'accuracy': self.personality.weapon_accuracy,
            'power': self.personality.weapon_power
        }

        self.ship.pending_weapon_animations.append(weapon_animation)
        self.ship.weapon_cooldown = constants.ENEMY_WEAPON_COOLDOWN_SECONDS * 1000
        self.ship.last_weapon_fire_time = current_time

    def move_toward_target(self):
        """Move closer to the target using hex-based navigation."""
        if not self.target or self.ship.is_moving:
            return

        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return

        current_hex = (int(self.ship.position[0]), int(self.ship.position[1]))
        target_hex = (int(target_pos[0]), int(target_pos[1]))

        dx = target_hex[0] - current_hex[0]
        dy = target_hex[1] - current_hex[1]

        if dx == 0 and dy == 0:
            return

        max_move_distance = int(self.personality.move_distance)
        move_distance = random.randint(1, max_move_distance)

        distance_to_target = math.sqrt(dx * dx + dy * dy)
        if distance_to_target > 0:
            unit_dx = dx / distance_to_target
            unit_dy = dy / distance_to_target

            new_hex_x = current_hex[0] + int(unit_dx * move_distance)
            new_hex_y = current_hex[1] + int(unit_dy * move_distance)

            if random.random() < self.personality.unpredictability:
                new_hex_x += random.randint(-1, 1)
                new_hex_y += random.randint(-1, 1)

            self.ship.start_movement((new_hex_x, new_hex_y))

    def move_away_from_target(self):
        """Move away from the target using hex-based navigation."""
        if not self.target or self.ship.is_moving:
            return

        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return

        current_hex = (int(self.ship.position[0]), int(self.ship.position[1]))
        target_hex = (int(target_pos[0]), int(target_pos[1]))

        dx = current_hex[0] - target_hex[0]
        dy = current_hex[1] - target_hex[1]

        max_move_distance = int(self.personality.move_distance)
        move_distance = random.randint(1, max_move_distance)

        distance_to_target = math.sqrt(dx * dx + dy * dy)
        if distance_to_target == 0:
            dx, dy = random.choice([
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (-1, -1), (1, -1), (-1, 1)
            ])
        else:
            dx = dx / distance_to_target
            dy = dy / distance_to_target

        new_hex_x = current_hex[0] + int(dx * move_distance)
        new_hex_y = current_hex[1] + int(dy * move_distance)

        if random.random() < self.personality.evasion_skill:
            new_hex_x += random.randint(-1, 1)
            new_hex_y += random.randint(-1, 1)

        self.ship.start_movement((new_hex_x, new_hex_y))

    def move_to_flank_position(self):
        """Move to a flanking position relative to target."""
        if not self.target or self.ship.is_moving:
            return

        target_pos = getattr(self.target, 'position', None)
        if not target_pos:
            return

        current_hex = (int(self.ship.position[0]), int(self.ship.position[1]))
        target_hex = (int(target_pos[0]), int(target_pos[1]))

        dx = target_hex[0] - current_hex[0]
        dy = target_hex[1] - current_hex[1]

        # Choose a perpendicular direction
        if random.random() < 0.5:
            flank_dx, flank_dy = -dy, dx
        else:
            flank_dx, flank_dy = dy, -dx

        flank_distance = int(self.preferred_range * 0.8)
        if flank_distance == 0:
            flank_distance = 2

        if flank_dx != 0 or flank_dy != 0:
            flank_length = math.sqrt(flank_dx * flank_dx + flank_dy * flank_dy)
            flank_dx = int((flank_dx / flank_length) * flank_distance)
            flank_dy = int((flank_dy / flank_length) * flank_distance)

        new_hex_x = target_hex[0] + flank_dx
        new_hex_y = target_hex[1] + flank_dy

        self.ship.start_movement((new_hex_x, new_hex_y))

    def move_randomly(self):
        """Random patrol movement."""
        if self.ship.is_moving:
            return

        current_hex = (int(self.ship.position[0]), int(self.ship.position[1]))

        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, -1), (1, -1), (-1, 1),
            (0, 0)
        ]

        direction = random.choice(directions)

        max_move_distance = int(self.personality.move_distance)
        move_distance = random.randint(1, max_move_distance)

        new_hex_x = current_hex[0] + (direction[0] * move_distance)
        new_hex_y = current_hex[1] + (direction[1] * move_distance)

        self.ship.start_movement((new_hex_x, new_hex_y))

    def _should_repair(self):
        """
        Determine if the ship should enter repair mode.
        Based on damage level and personality traits.
        """
        # Check if repair system exists
        if not hasattr(self.ship, 'repair_system'):
            return False

        # Check if ship needs repair
        if not self.ship.repair_system._needs_repair():
            return False

        # High shield_priority personalities are more likely to repair
        repair_threshold = 0.7 + (self.personality.shield_priority * 0.2)

        # Check system damage levels
        for system, integrity in self.ship.system_integrity.items():
            if system == 'hull':
                if integrity < self.ship.max_hull_strength * repair_threshold:
                    return True
            elif system != 'shields':  # Shields regenerate automatically
                if integrity < repair_threshold * 100:
                    return True

        return False

    def _execute_repair(self, current_time):
        """
        Execute repair state - start repairs and maintain distance from enemies.
        """
        # Start repairs if not already repairing
        if hasattr(self.ship, 'repair_system') and not self.ship.repair_system.is_repairing:
            if self.ship.repair_system.start_repairs():
                print(f"[KLINGON] {self.ship.name} initiating damage control procedures...")

        # Check if repairs are complete
        if hasattr(self.ship, 'repair_system') and not self.ship.repair_system._needs_repair():
            self.ship.repair_system.stop_repairs()
            print(f"[KLINGON] {self.ship.name} repairs complete. Resuming combat operations.")
            self.state = self.STATE_PATROL
            return

        # If enemy approaches while repairing, consider retreating or engaging
        if self.target:
            distance = self._get_distance_to_target()
            if distance < self.preferred_range:
                # Enemy too close - stop repairs and engage
                if hasattr(self.ship, 'repair_system'):
                    self.ship.repair_system.stop_repairs()
                print(f"[KLINGON] {self.ship.name} repairs interrupted - enemy too close!")
                self.state = self.STATE_ATTACK
                return
            elif distance < self.preferred_range * 1.5:
                # Enemy approaching - move away while repairing
                self.move_away_from_target()
