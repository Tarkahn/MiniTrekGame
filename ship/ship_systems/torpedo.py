import time
from data import constants
from ship.base_ship import BaseShip


class Torpedo:
    def __init__(self, power: int, speed: int, accuracy: float, ship: BaseShip):
        self.power = power
        self.speed = speed
        self.accuracy = accuracy  # e.g., 0.9 for 90% chance to hit at max range, or as a modifier
        self.ship = ship
        self.energy_cost = constants.TORPEDO_ENERGY_COST  # Energy consumed per torpedo fired
        self.max_power = constants.TORPEDO_MAX_POWER  # Max power for torpedo

    def fire(self, target_distance: int) -> int:
        """
        Fires a torpedo at a target, consuming energy.
        Returns the damage dealt, or 0 if unable to fire.
        For simplicity, this example assumes instant hit/miss based on accuracy and range.
        """
        if not self.ship.consume_energy(self.energy_cost):
            print(f"Insufficient energy on {self.ship.name} to fire torpedo.")
            return 0
        
        # Simple accuracy check based on distance
        hit_chance = max(0, self.accuracy - (target_distance * 0.05))  # Accuracy decreases with distance
        
        if hit_chance > 0 and time.time() % 1 < hit_chance:  # Simple random hit/miss for demonstration
            damage = self.power
            print(f"{self.ship.name} fired torpedo. Hit! Damage dealt: {damage}. Energy remaining: {self.ship.warp_core_energy}")
            return damage
        else:
            print(f"{self.ship.name} fired torpedo. Missed! Energy remaining: {self.ship.warp_core_energy}")
            return 0 