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
        
        # Movement personality parameters
        self.movement_speed = random.uniform(0.8, 1.2)  # Speed multiplier (0.8-1.2x of base speed)
        self.movement_distance = random.uniform(2.0, 6.0)  # Distance before changing direction (hex units)
        self.dwell_time = random.uniform(1.5, 4.0)  # Time to stay at location (seconds)
        self.maneuverability = random.uniform(0.5, 1.0)  # How often to change direction (0.5-1.0)
        
        # Movement state
        self.current_destination = None
        self.movement_start_time = None
        self.last_decision_time = time.time()
        self.movement_pattern = random.choice(["patrol", "circular", "evasive"])  # Movement behavior
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

    def set_target(self, target):
        self.target = target

    def update_ai(self, delta_time):
        """Update AI logic including movement and combat decisions"""
        current_time = time.time()
        
        # Update smooth movement animation
        self.update_movement_animation(delta_time)
        
        # Make movement decisions
        self.update_movement_decisions(current_time)
        
        # Combat AI if target exists
        if self.target and hasattr(self.target, 'is_alive') and self.target.is_alive():
            distance_to_target = self.calculate_distance(self.target.position)
            
            if distance_to_target < self.attack_range:
                self.fire_at_target(distance_to_target)
            elif distance_to_target < self.pursuit_range:
                self.pursue_target()

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
        """Set a new movement destination, constrained to hex grid"""
        # Constrain destination to grid boundaries and snap to hex centers
        constrained_dest = self.constrain_to_grid(destination[0], destination[1])
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
        """Enemy AI chooses weapon based on range or other factors"""
        if target_distance < self.phaser_system.range and not self.phaser_system.is_on_cooldown():
            damage = self.phaser_system.fire(target_distance)
            if damage > 0:
                self.target.apply_damage(damage)
        elif target_distance < 15 and not self.torpedo_system.is_on_cooldown():  # Example torpedo range
            damage = self.torpedo_system.fire(target_distance)
            if damage > 0:
                self.target.apply_damage(damage)

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