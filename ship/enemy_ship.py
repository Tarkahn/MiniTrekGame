from .base_ship import BaseShip
from data import constants
from ship.ship_systems.phaser import Phaser
from ship.ship_systems.torpedo import Torpedo


class EnemyShip(BaseShip):
    def __init__(self, name, max_shield_strength, hull_strength, energy, max_energy, weapons=None, position=None):
        super().__init__(name, max_shield_strength, hull_strength, energy, max_energy, weapons, position)
        self.target = None
        self.aggression_level = "medium"  # Can be "low", "medium", "high"
        self.pursuit_range = 500
        self.attack_range = 200
        self.phaser_system = Phaser(power=constants.ENEMY_PHASER_POWER, range=constants.ENEMY_PHASER_RANGE, ship=self)  # Example values
        self.torpedo_system = Torpedo(power=constants.ENEMY_TORPEDO_POWER, speed=constants.ENEMY_TORPEDO_SPEED, accuracy=constants.ENEMY_TORPEDO_ACCURACY, ship=self)  # Example values

    def set_target(self, target):
        self.target = target

    def update_ai(self):
        if not self.target or not self.target.is_alive():
            # Later: implement logic to find a new target
            return

        distance_to_target = self.calculate_distance(self.target.position)

        if distance_to_target < self.attack_range:
            self.fire_at_target(distance_to_target)
        elif distance_to_target < self.pursuit_range:
            self.pursue_target()
        else:
            self.patrol()  # Or some other non-combat behavior

    def calculate_distance(self, other_position):
        # Placeholder for distance calculation, assumes 2D Euclidean distance
        return ((self.position[0] - other_position[0])**2 + (self.position[1] - other_position[1])**2)**0.5

    def fire_at_target(self, target_distance):
        # Enemy AI chooses weapon based on range or other factors
        if target_distance < self.phaser_system.range and not self.phaser_system.is_on_cooldown():
            damage = self.phaser_system.fire(target_distance)
            if damage > 0:
                self.target.apply_damage(damage)
        elif target_distance < 15 and not self.torpedo_system.is_on_cooldown():  # Example torpedo range
            damage = self.torpedo_system.fire(target_distance)
            if damage > 0:
                self.target.apply_damage(damage)
        else:
            print(f"{self.name} cannot attack {self.target.name} at this time.")

    def pursue_target(self):
        # Basic pursuit logic, moving towards the target
        print(f"{self.name} is pursuing {self.target.name}.")
        # Calculate direction and move
        dx = self.target.position[0] - self.position[0]
        dy = self.target.position[1] - self.position[1]
        
        # Normalize direction vector and move a step
        magnitude = (dx**2 + dy**2)**0.5
        if magnitude > 0:
            move_speed = 5  # Placeholder speed
            self.position = (self.position[0] + dx/magnitude * move_speed,
                             self.position[1] + dy/magnitude * move_speed)

    def patrol(self):
        # Basic patrol logic, just staying put for now
        print(f"{self.name} is patrolling.")
        pass  # To be implemented with more complex patrol patterns 