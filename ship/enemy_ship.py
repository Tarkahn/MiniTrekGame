from .base_ship import BaseShip
from data.constants import *


class EnemyShip(BaseShip):
    def __init__(self, name, shield_strength, hull_strength, energy, max_energy, weapons, position):
        super().__init__(name, shield_strength, hull_strength, energy, max_energy, weapons, position)
        self.target = None
        self.aggression_level = "medium"  # Can be "low", "medium", "high"
        self.pursuit_range = 500
        self.attack_range = 200

    def set_target(self, target):
        self.target = target

    def update_ai(self):
        if not self.target or not self.target.is_alive():
            # Later: implement logic to find a new target
            return

        distance_to_target = self.calculate_distance(self.target.position)

        if distance_to_target < self.attack_range:
            self.fire_at_target()
        elif distance_to_target < self.pursuit_range:
            self.pursue_target()
        else:
            self.patrol()  # Or some other non-combat behavior

    def calculate_distance(self, other_position):
        # Placeholder for distance calculation, assumes 2D Euclidean distance
        return ((self.position[0] - other_position[0])**2 + (self.position[1] - other_position[1])**2)**0.5

    def fire_at_target(self):
        # Basic firing logic, will be expanded
        print(f"{self.name} is firing at {self.target.name}!")
        # For now, let's just apply some direct damage to the target
        if self.weapons and self.weapons[0].get('type') == 'phaser':
            damage = self.weapons[0].get('power', 10)  # Default phaser power
            self.target.apply_damage(damage)
        elif self.weapons and self.weapons[0].get('type') == 'torpedo':
            # Torpedo logic will be more complex later (accuracy, speed)
            damage = self.weapons[0].get('power', 20)  # Default torpedo power
            self.target.apply_damage(damage)

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