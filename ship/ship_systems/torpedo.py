import time
import random
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
        self.cooldown_seconds = 3.0  # 3 second cooldown between torpedoes
        self._last_fired_time = 0

    def is_on_cooldown(self) -> bool:
        return time.time() < self._last_fired_time + self.cooldown_seconds

    def fire(self, target_distance: int) -> int:
        """
        Fires a torpedo at a target, consuming energy and torpedo count.
        Returns the damage dealt, or 0 if unable to fire.
        For simplicity, this example assumes instant hit/miss based on accuracy and range.
        """
        if self.is_on_cooldown():
            return 0
        
        # Check if ship has torpedoes available
        if not self.ship.has_torpedoes():
            print(f"{self.ship.name} has no torpedoes remaining!")
            return 0
            
        if not self.ship.consume_energy(self.energy_cost):
            print(f"Insufficient energy on {self.ship.name} to fire torpedo.")
            return 0
        
        # Consume one torpedo
        if not self.ship.consume_torpedo():
            print(f"{self.ship.name} has no torpedoes remaining!")
            return 0
        
        self._last_fired_time = time.time()  # Set cooldown timer
        
        # Always calculate potential damage (hit/miss determined later during animation)
        damage = self.power
        
        # Check for critical hit
        is_critical_hit = random.random() < constants.CRITICAL_HIT_CHANCE
        if is_critical_hit:
            damage *= constants.CRITICAL_HIT_MULTIPLIER
            print("Critical Hit!")

        print(f"{self.ship.name} fired torpedo. Potential damage: {damage}. Torpedoes remaining: {self.ship.torpedo_count}. Energy remaining: {self.ship.warp_core_energy}")
        return damage 